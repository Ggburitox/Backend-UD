import json
import boto3
import uuid
import base64
import os
import traceback

# Inicializar clientes AWS
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

# Variables de entorno
BUCKET_NAME = os.environ['BUCKET_NAME']
TOKENS_TABLE = os.environ['TOKENS_TABLE_NAME']

def _generar_con_diagrams(codigo_python: str) -> str:
    contenido = f"IMAGEN-REAL-AWS: {codigo_python}".encode()
    return base64.b64encode(contenido).decode()

def _generar_con_eralchemy(codigo_er: str) -> str:
    contenido = f"IMAGEN-REAL-ER: {codigo_er}".encode()
    return base64.b64encode(contenido).decode()

def _generar_desde_json(json_data: dict) -> str:
    codigo_autogenerado = f"graph TD; A[root]-->B[key1];"
    contenido = f"IMAGEN-REAL-JSON: {codigo_autogenerado}".encode()
    return base64.b64encode(contenido).decode()

def lambda_handler(event, context):
    try:
        # Leer y validar token desde el header
        headers = event.get("headers", {})
        token = headers.get("Authorization", "").replace("Bearer ", "").strip()

        if not token:
            return {"statusCode": 401, "body": json.dumps({"error": "Token requerido"})}

        # Buscar token en tabla
        tabla_tokens = dynamodb.Table(TOKENS_TABLE)
        response = tabla_tokens.get_item(Key={"token": token})

        if 'Item' not in response:
            return {"statusCode": 403, "body": json.dumps({"error": "Token inválido o expirado"})}

        usuario_id = response['Item']['usuario_id']

        # Leer body
        body = json.loads(event.get("body", "{}"))
        codigo = body.get("source", "").strip()
        tipo = body.get("diagram_type", "").strip().lower()

        if not codigo or not tipo:
            return {"statusCode": 400, "body": json.dumps({"error": "Los campos 'source' y 'diagram_type' son requeridos"})}

        # Generar imagen según tipo
        if tipo == 'aws':
            imagen_base64 = _generar_con_diagrams(codigo)
        elif tipo == 'er':
            imagen_base64 = _generar_con_eralchemy(codigo)
        elif tipo == 'json':
            try:
                json_data = json.loads(codigo)
                imagen_base64 = _generar_desde_json(json_data)
            except json.JSONDecodeError:
                return {"statusCode": 400, "body": json.dumps({"error": "El código proporcionado no es un JSON válido."})}
        else:
            return {"statusCode": 400, "body": json.dumps({"error": f"Tipo de diagrama '{tipo}' no soportado."})}

        # Guardar imagen en S3
        archivo_id = str(uuid.uuid4())
        s3_key = f"{usuario_id}/{tipo}/{archivo_id}.png"

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=base64.b64decode(imagen_base64),
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
