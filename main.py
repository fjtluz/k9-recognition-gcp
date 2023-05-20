import requests
import json
import base64
import re
import os

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QFileDialog
from PyQt5.QtGui import QPixmap


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(800, 600)

        self.file_open_btn = QPushButton('Abrir arquivo')
        self.file_open_btn.clicked.connect(self.get_folder)

        self.analysis_btn = QPushButton('Analisar imagem')
        self.analysis_btn.clicked.connect(self.request_analysis)

        self.gen_random_btn = QPushButton('Gerar imagem aleatória')
        self.gen_random_btn.clicked.connect(self.fetch_random_dog)

        self.labelImage = QLabel()

        self.labelList = QLabel()
        self.labelList.resize(self.labelList.width(), 0)

        layout = QVBoxLayout()
        layout.addWidget(self.file_open_btn)
        layout.addWidget(self.gen_random_btn)
        layout.addWidget(self.labelImage)
        layout.addWidget(self.analysis_btn)
        layout.addWidget(self.labelList)
        self.setLayout(layout)

    def get_folder(self):
        image_url, _ = QFileDialog.getOpenFileName(
            self, 'Project Data', r"", "")

        convert_image_to_base64(f'{image_url}')
        self.labelImage.setPixmap(draw_picture_in_screen(image_url))

        self.clear_label_list()

    def fetch_random_dog(self):
        retrieve_random_dog()

        convert_image_to_base64('assets/temp-dog.jpg')
        self.labelImage.setPixmap(draw_picture_in_screen('assets/temp-dog.jpg'))

        self.clear_label_list()

    def request_analysis(self):
        global label_list
        global image_is_dog

        self.labelList.setText('Iniciando análise...')
        self.labelList.repaint()

        start_dog_recognition()

        label_text = '<h1>NÃO É UM CACHORRO</h1>'

        if image_is_dog:
            unordered_list = '<ul>#ITEMS#</ul>'
            list_items = ''
            for label in label_list:
                description = label['description']
                related = 'RACE' if description.upper() == 'DOG' else 'BREED'
                list_items += f"<li><h1>{related}: {description} - SCORE: {round(label['score'] * 100, 1)}%</h1></li>"

            label_text = unordered_list.replace('#ITEMS#', list_items)

        self.labelList.setText(label_text)

    def clear_label_list(self):
        self.labelList.setText('')
        self.labelList.repaint()


def draw_picture_in_screen(image_url):
    pixmap = QPixmap(f'{image_url}')

    if not pixmap.isNull():

        convert_image_to_base64(image_url)

        original_width = pixmap.width()
        original_height = pixmap.height()

        desired_width = original_width
        desired_height = original_height

        while desired_width > 500 or desired_height > 500:
            desired_width *= 0.9
            desired_height *= 0.9

        pixmap = pixmap.scaled(int(desired_width), int(desired_height))
    return pixmap


def is_dog():
    global image_is_dog
    global label_list

    for label in label_list:
        if label['description'].upper() == 'DOG':
            image_is_dog = True
            break
    else:
        image_is_dog = False


def filter_irrelevant():
    global label_list
    global breed_list

    is_dog()

    new_list = []

    for label in label_list:

        score = label['score']
        description = label['description'].upper()
        description = re.sub('[\s+]', '', description)

        if score > 0.5 and breed_list.count(description) != 0:
            new_list.append(label)

    label_list = new_list


def convert_image_to_base64(img_path):
    global image_as_b64

    with open(f'{img_path}', 'rb') as file:
        content = file.read()
        file.close()
        image_as_b64 = base64.b64encode(content).decode('ascii')


def start_dog_recognition():
    global api_key
    global image_as_b64
    global label_list

    if image_as_b64 is not None:

        url = 'https://vision.googleapis.com/v1/images:annotate'
        params = {'key': api_key}
        payload = {
            "requests": [
                {
                    "features": [
                        {
                            "maxResults": 50,
                            "type": "LABEL_DETECTION"
                        },
                    ],
                    "image": {
                        "content": f"{image_as_b64}"
                    }
                }
            ]
        }

        request = requests.post(url, params=params, data=json.dumps(payload))

        if request.status_code == 200:
            label_list = request.json()['responses'][0]['labelAnnotations']
            print(label_list)
            filter_irrelevant()


def retrieve_breed_list():
    global breed_list

    request = requests.get('https://dog.ceo/api/breeds/list/all')

    if request.status_code == 200:
        root: dict = request.json()['message']

        for breed in root:
            if len(root[breed]):
                for specific in root[breed]:
                    breed_list.append(f'{specific}{breed}'.upper())
            breed_list.append(breed.upper())

    breed_list.append('DOG')


def retrieve_random_dog():
    request = requests.get('https://dog.ceo/api/breeds/image/random')
    if request.status_code == 200:
        request = requests.get(request.json()['message'])
        image = request.content
        file = open('assets/temp-dog.jpg', 'wb')
        file.write(image)
        file.flush()


def retrieve_key(key_type: str):
    try:
        file = open('.keystore-dev', 'r')
    except OSError:
        file = open('.keystore', 'r')
    keys = file.read()
    file.close()

    if keys.count(key_type):
        start = keys.index(key_type) + len(key_type) + 1
        end = keys.index(';', start)
        return keys[start:end]

    return ''


if __name__ == '__main__':
    api_key = retrieve_key('gcp')

    image_is_dog = False
    image_as_b64 = None
    label_list = []
    breed_list = []

    retrieve_breed_list()

    app = QApplication([])
    main = MainWindow()
    main.show()
    app.exec()

    if os.path.isfile('assets/temp-dog.jpg'):
        os.remove('assets/temp-dog.jpg')

