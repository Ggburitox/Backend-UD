import json
import boto3
import uuid
import os
import traceback
from diagrams import Diagram, EC2, S3

# Inicializar clientes de AWS
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

# Leer variables de entorno
BUCKET_NAME = os.environ['BUCKET_NAME']
TOKENS_TABLE = os.environ['TOKENS_TABLE_NAME']

def generar_imagen_aws(path: str):
    """Genera una imagen PNG real usando diagrams."""
    with Diagram("Diagrama AWS Real", outformat="png", filename=path, show=False):
        S3("almacenamiento") >> EC2("servidor")

def lambda_handler(event, context):
    try:
        # Leer token del header
        headers = event.get("headers", {})
        token = headers.get("Authorization", "").replace("Bearer ", "").strip()

        if not token:
            return {"statusCode": 401, "body": json.dumps({"error": "Token requerido"})}

        # Validar token en la base de datos
        tabla_tokens = dynamodb.Table(TOKENS_TABLE)
        response = tabla_tokens.get_item(Key={"token": token})

        if 'Item' not in response:
            return {"statusCode": 403, "body": json.dumps({"error": "Token inválido o expirado"})}

        usuario_id = response['Item']['usuario_id']

        # Leer body del evento
        body = json.loads(event.get("body", "{}"))
        codigo = body.get("source", "").strip()
        tipo = body.get("diagram_type", "").strip().lower()

        if not codigo or not tipo:
            return {"statusCode": 400, "body": json.dumps({"error": "Los campos 'source' y 'diagram_type' son requeridos"})}

        # Preparar nombre y ruta del archivo
        archivo_id = str(uuid.uuid4())
        nombre_archivo = f"{archivo_id}.png"
        ruta_local = f"/tmp/{archivo_id}"
        s3_key = f"{usuario_id}/{tipo}/{nombre_archivo}"

        # Generar imagen según el tipo
        if tipo == "aws":
            generar_imagen_aws(ruta_local)
        else:
            return {"statusCode": 400, "body": json.dumps({"error": f"Tipo de diagrama '{tipo}' no soportado todavía."})}

        # Leer imagen desde disco
        with open(f"{ruta_local}.png", "rb") as f:
            imagen = f.read()

        # Subir a S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=imagen,
            ContentType='image/png'
        )

        # Devolver la URL pública
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
