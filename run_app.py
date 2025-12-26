import subprocess
import time
import webbrowser
import os
import signal
import sys
import platform

def run_project():
    print("🚀 NBA Game Predictor Launcher")
    print("------------------------------")

    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")

    p_backend = None
    p_frontend = None

    try:
        # 1. Start Backend
        print("🍳 Starting Backend (Kitchen)...")
        # Use shell=True for Windows compatibility with python command finding
        p_backend = subprocess.Popen(
            ["python", "main.py"], 
            cwd=backend_dir,
            shell=True
        )
        print("   -> Backend process created.")

        # 2. Start Frontend
        print("🍽️  Starting Frontend (Dining Room)...")
        # npm needs shell=True on Windows to resolve the cmd file
        p_frontend = subprocess.Popen(
            ["npm", "run", "dev"], 
            cwd=frontend_dir, 
            shell=True
        )
        print("   -> Frontend process created.")

        # 3. Wait for servers to spin up
        print("⏳ Waiting for servers to warm up (10 seconds)...")
        time.sleep(10)

        # 4. Open Browser
        url = "http://localhost:3000"
        print(f"🌍 Opening Browser: {url}")
        webbrowser.open(url)
        
        print("\n✅ App is running!")
        print("------------------------------")
        print("Press Ctrl+C to stop servers and exit.")
        print("------------------------------")

        # Keep script running
        p_backend.wait()
        p_frontend.wait()

    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Cleanup
        print("🧹 Cleaning up processes...")
        
        # Note: terminate() on Windows with shell=True might not kill the actual python/node children
        # deeply, but for a simple dev script this is usually "good enough" or we iterate.
        if p_backend:
            # On Windows, we often need taskkill to be sure if shell=True spawned a cmd wrapper
            if platform.system() == "Windows":
                 subprocess.call(['taskkill', '/F', '/T', '/PID', str(p_backend.pid)])
            else:
                 p_backend.terminate()
        
        if p_frontend:
            if platform.system() == "Windows":
                 subprocess.call(['taskkill', '/F', '/T', '/PID', str(p_frontend.pid)])
            else:
                 p_frontend.terminate()
        
        print("👋 Goodbye!")

if __name__ == "__main__":
    run_project()
