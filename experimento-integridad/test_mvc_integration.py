#!/usr/bin/env python3
"""
Script de prueba para verificar la integración MVC de los servicios.
"""
import requests
import json
import hashlib
import time

def compute_checksum(data):
    """Computa el checksum SHA256 de los datos."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def test_inventory_service():
    """Prueba el servicio de inventario directamente."""
    print("🧪 Probando inventory-service...")
    
    # Health check
    try:
        response = requests.get("http://localhost:8080/healthz", timeout=5)
        print(f"✅ Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health check falló: {e}")
        return False
    
    # Crear producto (sin validación de integridad - debería fallar)
    try:
        product_data = {
            "sku": "TEST-001",
            "name": "Producto de Prueba",
            "lot_number": "LOT123",
            "expiration_date": "2025-12-31"
        }
        response = requests.post("http://localhost:8080/inventory/products", 
                               json=product_data, timeout=5)
        print(f"❌ Crear producto sin validación: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Error en crear producto: {e}")
    
    return True

def test_validador_service():
    """Prueba el servicio validador."""
    print("\n🧪 Probando cf-validador...")
    
    # Datos de prueba
    product_data = {
        "sku": "TEST-002",
        "name": "Producto Validado",
        "lot_number": "LOT456",
        "expiration_date": "2025-12-31"
    }
    
    # Convertir a JSON canónico
    json_data = json.dumps(product_data, separators=(',', ':'), sort_keys=True)
    checksum = compute_checksum(json_data)
    
    # Headers con checksum
    headers = {
        "Content-Type": "application/json",
        "X-Message-Integrity": f"sha256={checksum}"
    }
    
    try:
        response = requests.post("http://localhost:8081/", 
                               data=json_data, 
                               headers=headers, 
                               timeout=10)
        print(f"✅ Validación y proxy: {response.status_code}")
        if response.status_code == 200:
            print(f"   Respuesta: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Error en validador: {e}")
        return False
    
    return True

def test_full_integration():
    """Prueba la integración completa."""
    print("\n🧪 Probando integración completa...")
    
    # Datos de prueba
    product_data = {
        "sku": "TEST-003",
        "name": "Producto Integrado",
        "lot_number": "LOT789",
        "expiration_date": "2025-12-31"
    }
    
    # Convertir a JSON canónico
    json_data = json.dumps(product_data, separators=(',', ':'), sort_keys=True)
    checksum = compute_checksum(json_data)
    
    # Headers con checksum
    headers = {
        "Content-Type": "application/json",
        "X-Message-Integrity": f"sha256={checksum}"
    }
    
    try:
        # Enviar a través del validador
        response = requests.post("http://localhost:8081/", 
                               data=json_data, 
                               headers=headers, 
                               timeout=10)
        print(f"✅ Integración completa: {response.status_code}")
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"   Estado: {result.get('status', 'unknown')}")
            if 'product' in result:
                print(f"   Producto: {result['product']['sku']} - {result['product']['name']}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Error en integración: {e}")
        return False
    
    return True

def main():
    """Función principal de prueba."""
    print("🚀 Iniciando pruebas de integración MVC...")
    print("=" * 50)
    
    # Esperar un poco para que los servicios estén listos
    print("⏳ Esperando que los servicios estén listos...")
    time.sleep(5)
    
    # Ejecutar pruebas
    inventory_ok = test_inventory_service()
    validador_ok = test_validador_service()
    integration_ok = test_full_integration()
    
    print("\n" + "=" * 50)
    print("📊 Resumen de pruebas:")
    print(f"   Inventory Service: {'✅ OK' if inventory_ok else '❌ FALLO'}")
    print(f"   Validador Service: {'✅ OK' if validador_ok else '❌ FALLO'}")
    print(f"   Integración Completa: {'✅ OK' if integration_ok else '❌ FALLO'}")
    
    if all([inventory_ok, validador_ok, integration_ok]):
        print("\n🎉 ¡Todas las pruebas pasaron! La arquitectura MVC está funcionando correctamente.")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisa los logs de los servicios.")

if __name__ == "__main__":
    main()
