#!/usr/bin/env python3
"""
Test específico para WebSearchTool con Serper.dev API
"""

import os
from dotenv import load_dotenv
from blog_automation import WebSearchTool

def test_websearch_direct():
    """Test directo de la herramienta WebSearch"""
    print("🔍 Testing WebSearchTool directamente...")
    
    load_dotenv()
    
    # Verificar API key
    serper_key = os.getenv("SERPER_API_KEY")
    if not serper_key:
        print("❌ SERPER_API_KEY no encontrada en .env")
        return False
    
    print(f"✅ API Key encontrada: {serper_key[:10]}...{serper_key[-4:]}")
    
    # Crear y probar herramienta
    try:
        web_tool = WebSearchTool()
        print("✅ WebSearchTool creado exitosamente")
        
        # Test con query específica
        test_query = "tendencias IA para PyMEs 2025"
        print(f"\n🔎 Probando búsqueda: '{test_query}'")
        
        result = web_tool._run(test_query)
        
        print("\n📊 RESULTADO:")
        print("=" * 60)
        print(result)
        print("=" * 60)
        
        if "Error" in result:
            print("❌ La búsqueda falló")
            return False
        elif "Title:" in result and "Summary:" in result:
            print("✅ Búsqueda exitosa - formato correcto")
            return True
        else:
            print("⚠️ Búsqueda devolvió datos pero formato inesperado")
            return False
            
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

def main():
    """Ejecuta test de WebSearch"""
    print("🤖 Test WebSearchTool con Serper.dev")
    print("=" * 50)
    
    success = test_websearch_direct()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡WebSearchTool funcionando correctamente!")
        print("💡 El sistema puede ejecutarse: python blog_automation.py")
    else:
        print("❌ Problemas con WebSearchTool")
        print("🔧 Revisa los logs de debug arriba para diagnosis")

if __name__ == "__main__":
    main() 