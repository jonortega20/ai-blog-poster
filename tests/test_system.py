#!/usr/bin/env python3
"""
Test script para verificar que el sistema de CrewAI funciona correctamente
"""

import os
from dotenv import load_dotenv

def test_environment():
    """Verifica que las variables de entorno estén configuradas"""
    print("🔍 Testing environment setup...")
    
    load_dotenv()
    
    required_vars = ["OPENAI_API_KEY", "SERPER_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {'*' * 10}...{value[-4:]}")
    
    if missing_vars:
        print(f"❌ Faltan variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environment setup correcto!")
    return True

def test_imports():
    """Verifica que todas las importaciones funcionen"""
    print("\n🔍 Testing imports...")
    
    try:
        from crewai import Agent, Task, Crew
        print("✅ CrewAI importado correctamente")
        
        from blog_automation import BlogAutomationCrew, WebSearchTool, FileWriterTool
        print("✅ Blog automation classes importadas")
        
        return True
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False

def test_tools():
    """Verifica que las herramientas personalizadas funcionen"""
    print("\n🔍 Testing custom tools...")
    
    try:
        from blog_automation import WebSearchTool, FileWriterTool
        
        # Test WebSearchTool initialization
        web_tool = WebSearchTool()
        print("✅ WebSearchTool creado correctamente")
        
        # Test FileWriterTool initialization  
        file_tool = FileWriterTool()
        print("✅ FileWriterTool creado correctamente")
        
        return True
    except Exception as e:
        print(f"❌ Error en herramientas: {e}")
        return False

def test_crew_creation():
    """Verifica que se pueda crear el crew sin errores"""
    print("\n🔍 Testing crew creation...")
    
    try:
        from blog_automation import BlogAutomationCrew
        
        automation = BlogAutomationCrew()
        print("✅ BlogAutomationCrew instanciado")
        
        # Test agent creation
        research_agent = automation.create_research_agent()
        print("✅ Research Agent creado")
        
        writer_agent = automation.create_writer_agent()
        print("✅ Writer Agent creado")
        
        qa_agent = automation.create_qa_agent()
        print("✅ QA Agent creado")
        
        technical_agent = automation.create_technical_agent()
        print("✅ Technical Agent creado")
        
        return True
    except Exception as e:
        print(f"❌ Error creando crew: {e}")
        return False

def main():
    """Ejecuta todos los tests"""
    print("🤖 Blog Automation System - Test Suite")
    print("=" * 50)
    
    tests = [
        test_environment,
        test_imports, 
        test_tools,
        test_crew_creation
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"\n❌ Test falló: {test.__name__}")
            break
    
    print("\n" + "=" * 50)
    if passed == len(tests):
        print("🎉 ¡Todos los tests pasaron! Sistema listo para ejecutar.")
        print("\n💡 Siguiente paso: python blog_automation.py")
    else:
        print(f"❌ {passed}/{len(tests)} tests pasaron. Revisa la configuración.")
    
    return passed == len(tests)

if __name__ == "__main__":
    main() 