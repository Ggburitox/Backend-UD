import json
import boto3
import os
import base64
from datetime import datetime

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

BUCKET_NAME = os.environ['BUCKET_NAME']
TOKENS_TABLE = os.environ['TOKENS_TABLE_NAME']

def verificar_token(token):
    tabla_tokens = dynamodb.Table(TOKENS_TABLE)
    response = tabla_tokens.get_item(Key={"token": token})
    if 'Item' not in response:
        raise Exception("Token inválido o expirado")
    return response['Item']['usuario_id']

def lambda_handler(event, context):
    try:
        headers = event.get("headers", {})
        token = headers.get("Authorization", "").replace("Bearer ", "").strip()

        if not token:
            return {"statusCode": 401, "body": json.dumps({"error": "Token requerido"})}

        usuario_id = verificar_token(token)

        body = json.loads(event.get("body", "{}"))
        archivo_id = body.get("archivo_id")
        tipo = body.get("tipo")

        if not archivo_id or not tipo:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "'archivo_id' y 'tipo' son requeridos"})
            }

        s3_key = f"{usuario_id}/{tipo}/{archivo_id}.png"
        response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        contenido = response['Body'].read()
        imagen_base64 = base64.b64encode(contenido).decode()

        return {
            "statusCode": 200,
            "body": json.dumps({
                "imagen_base64": f"data:image/png;base64,{imagen_base64}"
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
