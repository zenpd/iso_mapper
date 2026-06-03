#!/usr/bin/env python3
"""
ISO 20022 GenAI Migration Platform - Project Setup Script

This script organizes all platform files from a flat directory structure
into the proper project layout with packages and modules.

Usage:
    python setup.py

Before running, ensure all these files are in the same directory as setup.py:
    - main.py
    - streamlit_app.py
    - settings.py
    - schemas.py
    - llm_service.py
    - orchestrator.py
    - parser_agent.py
    - mapping_agent.py
    - enrichment_agent.py
    - validation_agent.py
    - requirements.txt
    - .env.example
    - README.md
    - utils_init.py (will become utils/__init__.py)
"""

import os
import shutil
from pathlib import Path

# Project structure definition
PROJECT_NAME = "mt_mx_platform"

# Directory structure
DIRECTORIES = [
    "agents",
    "config", 
    "models",
    "services",
    "utils"
]

# File mappings: source_filename -> destination_path
FILE_MAPPINGS = {
    # Agents
    "parser_agent.py": "agents/parser_agent.py",
    "mapping_agent.py": "agents/mapping_agent.py",
    "enrichment_agent.py": "agents/enrichment_agent.py",
    "validation_agent.py": "agents/validation_agent.py",
    
    # Config
    "settings.py": "config/settings.py",
    
    # Models
    "schemas.py": "models/schemas.py",
    
    # Services
    "llm_service.py": "services/llm_service.py",
    "orchestrator.py": "services/orchestrator.py",
    
    # Utils (special handling - the file contains sample data)
    "utils_init.py": "utils/__init__.py",
    
    # Root level files
    "main.py": "main.py",
    "streamlit_app.py": "streamlit_app.py",
    "requirements.txt": "requirements.txt",
    ".env.example": ".env.example",
    "README.md": "README.md",
}

# __init__.py content for each package
INIT_FILES = {
    "agents/__init__.py": '''from .parser_agent import MTParserAgent
from .mapping_agent import MappingAgent
from .enrichment_agent import EnrichmentAgent
from .validation_agent import ValidationAgent

__all__ = [
    "MTParserAgent",
    "MappingAgent",
    "EnrichmentAgent",
    "ValidationAgent"
]
''',
    
    "config/__init__.py": '''from .settings import settings, get_settings, Settings

__all__ = ["settings", "get_settings", "Settings"]
''',
    
    "models/__init__.py": '''from .schemas import (
    TransformationApproach,
    AgentStatus,
    MappedField,
    AgentResult,
    ParsedMTMessage,
    MappingResult,
    EnrichmentResult,
    ValidationError,
    ValidationResult,
    MXOutput,
    TransformationState,
    TransformationRequest,
    TransformationResponse,
    SampleMessage
)

__all__ = [
    "TransformationApproach",
    "AgentStatus",
    "MappedField",
    "AgentResult",
    "ParsedMTMessage",
    "MappingResult",
    "EnrichmentResult",
    "ValidationError",
    "ValidationResult",
    "MXOutput",
    "TransformationState",
    "TransformationRequest",
    "TransformationResponse",
    "SampleMessage"
]
''',
    
    "services/__init__.py": '''from .llm_service import llm_service, LLMService
from .orchestrator import orchestrator, TransformationOrchestrator

__all__ = [
    "llm_service",
    "LLMService",
    "orchestrator",
    "TransformationOrchestrator"
]
'''
}


def print_banner():
    """Print setup banner"""
    print("=" * 60)
    print("🔄 ISO 20022 GenAI Migration Platform - Setup")
    print("=" * 60)
    print()


def check_source_files():
    """Check if all required source files exist"""
    print("📋 Checking source files...")
    
    missing_files = []
    optional_files = [".env.example", "README.md", "utils_init.py"]
    
    for source_file in FILE_MAPPINGS.keys():
        if not os.path.exists(source_file):
            if source_file in optional_files:
                print(f"   ⚠️  Optional file not found: {source_file}")
            else:
                missing_files.append(source_file)
                print(f"   ❌ Missing: {source_file}")
        else:
            print(f"   ✅ Found: {source_file}")
    
    if missing_files:
        print(f"\n❌ Error: {len(missing_files)} required file(s) missing!")
        print("Please ensure all files are in the current directory.")
        return False
    
    print("\n✅ All required files found!\n")
    return True


def create_project_structure():
    """Create project directory structure"""
    print(f"📁 Creating project structure: {PROJECT_NAME}/")
    
    # Create main project directory
    project_path = Path(PROJECT_NAME)
    if project_path.exists():
        print(f"   ⚠️  Directory '{PROJECT_NAME}' already exists.")
        response = input("   Overwrite? (y/n): ").strip().lower()
        if response != 'y':
            print("   ❌ Setup cancelled.")
            return None
        shutil.rmtree(project_path)
    
    project_path.mkdir()
    print(f"   ✅ Created: {PROJECT_NAME}/")
    
    # Create subdirectories
    for directory in DIRECTORIES:
        dir_path = project_path / directory
        dir_path.mkdir()
        print(f"   ✅ Created: {PROJECT_NAME}/{directory}/")
    
    print()
    return project_path


def move_files(project_path: Path):
    """Move files to their destinations"""
    print("📦 Moving files to project structure...")
    
    moved_count = 0
    skipped_count = 0
    
    for source_file, dest_path in FILE_MAPPINGS.items():
        source = Path(source_file)
        destination = project_path / dest_path
        
        if source.exists():
            # Copy file (not move, to preserve originals)
            shutil.copy2(source, destination)
            print(f"   ✅ {source_file} → {PROJECT_NAME}/{dest_path}")
            moved_count += 1
        else:
            print(f"   ⏭️  Skipped (not found): {source_file}")
            skipped_count += 1
    
    print(f"\n   Moved: {moved_count} files")
    if skipped_count > 0:
        print(f"   Skipped: {skipped_count} files")
    print()
    
    return moved_count


def create_init_files(project_path: Path):
    """Create __init__.py files for packages"""
    print("📝 Creating __init__.py files...")
    
    for init_path, content in INIT_FILES.items():
        file_path = project_path / init_path
        
        # Don't overwrite if utils/__init__.py was moved from utils_init.py
        if init_path == "utils/__init__.py" and file_path.exists():
            print(f"   ⏭️  Skipped (already exists): {init_path}")
            continue
        
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"   ✅ Created: {PROJECT_NAME}/{init_path}")
    
    # Create utils/__init__.py if it doesn't exist
    utils_init = project_path / "utils/__init__.py"
    if not utils_init.exists():
        # Create a basic utils init with sample data
        with open(utils_init, 'w') as f:
            f.write('''"""
Utility functions and sample data
"""

from typing import List
from models import SampleMessage


def get_sample_messages() -> List[SampleMessage]:
    """Get sample MT103 messages for demo"""
    return [
        SampleMessage(
            id="MT103-001",
            name="Standard USD Transfer",
            description="Corporate payment to trading partner",
            currency="USD",
            amount="50,000.00",
            message=""":20:TRX2024112001
:23B:CRED
:32A:241118USD50000,00
:50K:/123456789
ACME CORPORATION
123 BUSINESS STREET
NEW YORK, NY 10001
:52A:CHASUS33XXX
:59:/987654321
GLOBAL TRADING LTD
456 COMMERCE AVENUE
LONDON, EC2R 8AH
:70:INVOICE INV-2024-1234
:71A:SHA"""
        ),
        SampleMessage(
            id="MT103-002",
            name="High Value EUR Transfer",
            description="Manufacturing equipment payment",
            currency="EUR",
            amount="2,500,000.00",
            message=""":20:TRX2024112002
:23B:CRED
:32A:241118EUR2500000,00
:50K:/DE89370400440532013000
DEUTSCHE MANUFACTURING GMBH
:52A:DEUTDEFFXXX
:59:/GB82WEST12345698765432
BRITISH IMPORTS PLC
:70:CONTRACT CON-2024-5678
:71A:OUR"""
        )
    ]


def format_duration(ms: int) -> str:
    """Format duration in human-readable format"""
    if ms < 1000:
        return f"{ms}ms"
    elif ms < 60000:
        return f"{ms/1000:.1f}s"
    else:
        return f"{ms/60000:.1f}m"
''')
        print(f"   ✅ Created: {PROJECT_NAME}/utils/__init__.py (default)")
    
    print()


def create_env_example(project_path: Path):
    """Create .env.example if it doesn't exist"""
    env_file = project_path / ".env.example"
    
    if not env_file.exists():
        print("📝 Creating .env.example...")
        
        content = '''# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com/"
AZURE_API_KEY="your-api-key-here"
CHAT_LLM_DEPLOYMENT="your-deployment-name"
CHAT_LLM_MODEL="gpt-4o"
AZURE_API_VERSION="2024-02-15-preview"

# Application Configuration
LOG_LEVEL="INFO"
TRANSFORMATION_APPROACH="hybrid"

# Performance Settings
LLM_TIMEOUT=30
LLM_MAX_RETRIES=3
CACHE_ENABLED=true
'''
        
        with open(env_file, 'w') as f:
            f.write(content)
        print(f"   ✅ Created: {PROJECT_NAME}/.env.example")
        print()


def print_summary(project_path: Path):
    """Print setup summary and next steps"""
    print("=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print()
    print(f"📁 Project created at: ./{PROJECT_NAME}/")
    print()
    print("📋 Project Structure:")
    print(f"   {PROJECT_NAME}/")
    print("   ├── agents/           # AI Agents")
    print("   ├── config/           # Configuration")
    print("   ├── models/           # Data Models")
    print("   ├── services/         # Core Services")
    print("   ├── utils/            # Utilities")
    print("   ├── main.py           # FastAPI Backend")
    print("   ├── streamlit_app.py  # Streamlit UI")
    print("   ├── requirements.txt  # Dependencies")
    print("   └── .env.example      # Environment Template")
    print()
    print("🚀 Next Steps:")
    print()
    print(f"   1. cd {PROJECT_NAME}")
    print()
    print("   2. Create virtual environment:")
    print("      python -m venv venv")
    print("      source venv/bin/activate  # Linux/Mac")
    print("      .\\venv\\Scripts\\activate   # Windows")
    print()
    print("   3. Install dependencies:")
    print("      pip install -r requirements.txt")
    print()
    print("   4. Configure Azure OpenAI:")
    print("      cp .env.example .env")
    print("      # Edit .env with your credentials")
    print()
    print("   5. Start the platform:")
    print("      # Terminal 1 - API")
    print("      uvicorn main:app --reload --port 8000")
    print()
    print("      # Terminal 2 - UI")
    print("      streamlit run streamlit_app.py --server.port 8501")
    print()
    print("   6. Access:")
    print("      UI:       http://localhost:8501")
    print("      API Docs: http://localhost:8000/docs")
    print()
    print("=" * 60)


def cleanup_option():
    """Offer to clean up source files"""
    print()
    response = input("🗑️  Delete original source files? (y/n): ").strip().lower()
    
    if response == 'y':
        print("\n   Cleaning up source files...")
        for source_file in FILE_MAPPINGS.keys():
            if os.path.exists(source_file):
                os.remove(source_file)
                print(f"   🗑️  Deleted: {source_file}")
        print("\n   ✅ Cleanup complete!")
    else:
        print("\n   ⏭️  Source files preserved.")


def main():
    """Main setup function"""
    print_banner()
    
    # Check source files
    if not check_source_files():
        return 1
    
    # Create project structure
    project_path = create_project_structure()
    if not project_path:
        return 1
    
    # Move files
    move_files(project_path)
    
    # Create __init__.py files
    create_init_files(project_path)
    
    # Create .env.example if needed
    create_env_example(project_path)
    
    # Print summary
    print_summary(project_path)
    
    # Offer cleanup
    cleanup_option()
    
    return 0


if __name__ == "__main__":
    exit(main())