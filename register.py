import json
import boto3
import hashlib
import uuid
import os
from datetime import datetime, timedelta

dynamodb = boto3.resource("dynamodb")
USERS_TABLE = os.environ.get("USERS_TABLE_NAME")

def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        email = body.get("email")
        password = body.get("password")
        username = body.get("username")

        if not email or not password or not username:
            return {
                'statusCode': 400,
                'headers': {"Access-Control-Allow-Origin": "*"},
                'body': json.dumps({'error': 'Email, contraseña y nombre de usuario son requeridos'})
            }

        usuario_id = email
        tabla_usuarios = dynamodb.Table(USERS_TABLE)

        if 'Item' in tabla_usuarios.get_item(Key={'usuario_id': usuario_id}):
            return {
                'statusCode': 409,
                'headers': {"Access-Control-Allow-Origin": "*"},
                'body': json.dumps({'error': 'El usuario ya existe'})
            }

        salt = uuid.uuid4().hex
        password_hash = hash_password(password, salt)

        nuevo_usuario = {
            'usuario_id': usuario_id,
            'username': username,
            'password': password_hash,
            'salt': salt,
        }

        tabla_usuarios.put_item(Item=nuevo_usuario)

        return {
            'statusCode': 201,
            'headers': {"Access-Control-Allow-Origin": "*"},
            'body': json.dumps({"message": "Usuario registrado correctamente"})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {"Access-Control-Allow-Origin": "*"},
            'body': json.dumps({'error': str(e)})
        }
