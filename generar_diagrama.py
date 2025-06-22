import json
import boto3
import uuid
import os
import base64
import traceback

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

BUCKET_NAME = os.environ['BUCKET_NAME']
TOKENS_TABLE = os.environ['TOKENS_TABLE_NAME']

def generar_imagen_simulada(contenido: str) -> bytes:
    # Simula una imagen PNG desde texto (base64 dummy)
    texto = f"IMAGEN-SIMULADA-AWS: {contenido}".encode("utf-8")
    return base64.b64encode(texto)

def lambda_handler(event, context):
    try:
        headers = event.get("headers", {})
        token = headers.get("Authorization", "").replace("Bearer ", "").strip()

        if not token:
            return {"statusCode": 401, "body": json.dumps({"error": "Token requerido"})}

        tabla_tokens = dynamodb.Table(TOKENS_TABLE)
        response = tabla_tokens.get_item(Key={"token": token})

        if 'Item' not in response:
            return {"statusCode": 403, "body": json.dumps({"error": "Token inválido o expirado"})}

        usuario_id = response['Item']['usuario_id']
        body = json.loads(event.get("body", "{}"))
        codigo = body.get("source", "").strip()
        tipo = body.get("diagram_type", "").strip().lower()

        if not codigo or not tipo:
            return {"statusCode": 400, "body": json.dumps({"error": "Los campos 'source' y 'diagram_type' son requeridos"})}

        archivo_id = str(uuid.uuid4())
        s3_key = f"{usuario_id}/{tipo}/{archivo_id}.png"

        if tipo == "aws":
            imagen_base64 = generar_imagen_simulada(codigo)
        else:
            return {"statusCode": 400, "body": json.dumps({"error": f"Tipo de diagrama '{tipo}' no soportado aún."})}

        imagen_bytes = base64.b64decode(imagen_base64)

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=imagen_bytes,
            ContentType='image/png'
        )

        image_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
        return {
            "statusCode": 200,
            "body": json.dumps({
                "imageUrl": image_url,
                "archivo_id": archivo_id
            })
        }

    except Exception as e:
        print(f"Error inesperado: {str(e)}\n{traceback.format_exc()}")
        return {"statusCode": 500, "body": json.dumps({"error": "Ocurrió un error interno en el servidor."})}
