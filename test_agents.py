import os
import sys

# Ensure correct python path so agents package is found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agents.orchestrator import EasyApplierOrchestrator
    print("[SUCCESS] Multi-agent orchestration files loaded and parsed correctly!")
    
    # Initialize Orchestrator to trigger auto-creation of default prompts under prompts/ directory
    orch = EasyApplierOrchestrator()
    print("[SUCCESS] Orchestrator and child agents initialized successfully!")
    
    # Let's list files in prompts/ to verify creation
    prompts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
    if os.path.exists(prompts_dir):
        print("[INFO] Prompts directory created. Files:")
        for f in os.listdir(prompts_dir):
            print(f"  - {f}")
    else:
        print("[WARNING] Prompts directory not found!")
        
except Exception as e:
    print(f"[ERROR] Import/initialization failed: {e}")
    sys.exit(1)
