python -m venv ./venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python setup.py
echo ./venv/bin/python mainv2.py > run.sh
echo read -n 1 -p "Input Selection:" "mainmenuinput" >> run.sh
chmod +x run.sh