python -m venv ./venv
"venv/Scripts/pip" install -r requirements.txt
"venv/Scripts/python" setup.py
echo "venv/Scripts/python" mainv2.py > run.bat 
echo pause >> run.bat