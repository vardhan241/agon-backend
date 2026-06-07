python3 - << 'EOF'
content = """#!/bin/bash
PORT=8001
echo "Freeing port $PORT..."
sudo lsof -ti:$PORT | xargs sudo kill -9 2>/dev/null
sleep 1
cd ~/Downloads/agon-agent_1-88fc36cc/backend
echo "Python: $(python3 --version)"
echo "Starting FastAPI..."
python3 -m uvicorn api:app --port $PORT --host 0.0.0.0 --workers 1
"""
with open('/Users/vardhan/Downloads/agon-agent_1-88fc36cc/start.sh', 'w') as f:
    f.write(content)
print("start.sh updated!")
EOF
chmod +x ~/Downloads/agon-agent_1-88fc36cc/start.sh