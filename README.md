# Тестовое задание для Lesta Game Start


### Description
Реализовать веб-приложение. В качестве интерфейса сделать страницу с формой для загрузки текстового файла, после загрузки и обработки файла отображается таблица с 50 словами с колонками:
- слово
- tf, сколько раз это слово встречается в тексте
- idf, обратная частота документа 

Вывод упорядочить по уменьшению idf.


### Technology stack
- fastapi 0.115.0
- Jinja2 3.1.6
- python-multipart 0.0.20
- uvicorn 0.32.1


### Project run
- Upgrade pip:  
```
python.exe -m pip install --upgrade pip
```

- Install dependencies from requirements.txt:  
```
pip install -r requirements.txt
```

- Run the application:  
```
py main.py
```
