import boto3
import hashlib
import uuid
import json
import os
from datetime import datetime, timedelta

def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()

def lambda_handler(event, context):
    try:
        USERS_TABLE = os.environ['USERS_TABLE_NAME']
        TOKENS_TABLE = os.environ['TOKENS_TABLE_NAME']

        body = json.loads(event.get("body", "{}"))
        email = body.get("email")
        password = body.get("password")

        if not email or not password:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Email y contraseña son requeridos'})
            }

        usuario_id = email

        dynamodb = boto3.resource('dynamodb')
        tabla_usuarios = dynamodb.Table(USERS_TABLE)
        response = tabla_usuarios.get_item(Key={'usuario_id': usuario_id})

        if 'Item' not in response:
            return {
                'statusCode': 403,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Usuario no existe o credenciales incorrectas'})
            }

        stored_password_hash = response['Item'].get('password')
        stored_salt = response['Item'].get('salt')

        if not stored_password_hash or not stored_salt:
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Error de configuración de usuario en la base de datos.'})
            }

        password_to_check_hash = hash_password(password, stored_salt)

        if password_to_check_hash != stored_password_hash:
            return {
                'statusCode': 403,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Usuario no existe o credenciales incorrectas'})
            }

        token = str(uuid.uuid4())
        expiration = datetime.utcnow() + timedelta(hours=1)

        registro_token = {
            'token': token,
            'usuario_id': usuario_id,
            'expires': expiration.strftime('%Y-%m-%d %H:%M:%S')
        }

        tabla_tokens = dynamodb.Table(TOKENS_TABLE)
        tabla_tokens.put_item(Item=registro_token)

        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({"token": token})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Ocurrió un error interno en el servidor.'})
        }
