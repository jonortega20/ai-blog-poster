#!/usr/bin/env python3
"""
Test WebSearchTool con campo 'description' como usa CrewAI
"""

import os
from dotenv import load_dotenv
from blog_automation import WebSearchTool

def test_websearch_with_description():
    """Test WebSearchTool usando campo description"""
    print("🔍 Testing WebSearchTool con campo 'description'...")
    
    load_dotenv()
    
    try:
        web_tool = WebSearchTool()
        print("✅ WebSearchTool creado")
        
        # Test con description (como usa CrewAI)
        result = web_tool._run(query="", description="tendencias IA para PyMEs 2025")
        
        print("\n📊 RESULTADO con field 'description':")
        print("=" * 60)
        print(result)
        print("=" * 60)
        
        if "Error" in result:
            print("❌ Falló con campo description")
            return False
        elif "Title:" in result and "Summary:" in result:
            print("✅ ¡Éxito con campo description!")
            return True
        else:
            print("⚠️ Respuesta inesperada")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🤖 Test WebSearchTool - Campo Description")
    print("=" * 50)
    
    success = test_websearch_with_description()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡WebSearchTool compatible con CrewAI!")
        print("💡 Ahora debería funcionar: python blog_automation.py")
    else:
        print("❌ Aún hay problemas con el formato description") 