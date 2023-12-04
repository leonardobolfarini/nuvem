import cv2
import streamlink
import pytesseract
import pymysql
# import serial, comentado pois não está sendo utilizado na nuvem
import time
import sys
from datetime import datetime

# arduino = serial.Serial("COM6", 9600), comentado pois n funciona em nuvem
# dar retorno pro deploy da nuvem
log_cloud = 'deploy.log'
with open(log_cloud, 'w') as log:
    sys.stdout = log
    print('Iniciando deploy...')

# classe que faz conexão com banco de dados
class Database:
    _host:str
    _user:str
    _port:int
    _password:str
    _database:str

    def __init__(self):
        self._host = None
        self._user = None
        self._password = None
        self._database = None   

    # método de classe para gerar conexão com o banco de dados
    @classmethod
    def _connect(cls):
        try:
            connection = pymysql.connect(
                host=cls._host,
                user=cls._user,
                password=cls._password,
                database=cls._database
            )
            return connection
        except: # gera log de deploy
            with open(log_cloud, 'w') as log:
                sys.stdout = log
                print('Não foi possivel estabelecer a conexão com o banco de dados')

# classe que faz manipulação de imagens
class Imagem:
    # Captura o frame da webcam
    def _ImageCapture(self):
        try:
            # url utilizada para capturar frame
            url = "https://www.twitch.tv/callmedigo"
            streams = streamlink.streams(url)
            url = streams["best"].url
        # parâmetro passado se refere a qual webcam será capturada a imagem
            cap = cv2.VideoCapture(url)
            _, frame = cap.read()
            time.sleep(2)
            return frame
        except:
            return None
            
    # método que acha os contornos no frame 
    def _contorno_imagem(self, frame):
        if frame is not None:
            # parâmetros são o frame passado para o método e o tamanho a ser redimensionalizado
            image_resized = cv2.resize(frame, (800, 400))
            # imagem a ser convertida e a função presente na biblioteca de conversão para cinza
            gray_image = cv2.cvtColor(image_resized, cv2.COLOR_BGR2GRAY)
            # função para binarizar a imagem
            _, binary_image = cv2.threshold(gray_image, 90, 255, 0)
            # função para borrar a imagem levemente
            blur_img = cv2.GaussianBlur(binary_image, (3, 3), 0)
            # função para fazer os contornos na imagem com base em árvore de hierarquia e todos os contornos são mantidos sem qualquer simplificação
            contours, _ = cv2.findContours(blur_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

            for contour in contours:
                # calcula o comprimento de cada contorno, caso este seja fechado (True)
                perimeter = cv2.arcLength(contour, True)
                if perimeter > 300: 
                    # aproxima o contorno simplificando-o, caso o valor seja menor no segundo parâmetro, mais proximo ficara do contorno original e True indica que é fechado
                    aprox_retangulo = cv2.approxPolyDP(contour, 0.03 * perimeter, True)
                    # caso a variavel tenha 4 lados (retangulo)
                    if len(aprox_retangulo) == 4:
                        # pega as coordenadas do contorno
                        x, y, height, width = cv2.boundingRect(contour)
                        # pinta um retangulo com essas coordenadas em cima da imagem passada, os dois ultimos parâmetros são a cor RGB e a grossura da linha
                        cv2.rectangle(image_resized, (x, y), (x + height, y + width), (90, 255, 35), 3)
                        roi = image_resized[y:y + width, x:x +height]
                        return roi
    
    # método que faz processos para facilitar para o tesseract achar a string
    def _preProcessamentoRoi(self, roi):
        max_width = 800
        max_height = 400    
        if roi is None:
            return 
        
        # pega o valor em pixels da imagem
        current_height, current_width = roi.shape[:2]
        # se for maior que o definido é redimensionado
        if current_width > max_width or current_height > max_height:
            roi = cv2.resize(roi, (max_width, max_height), interpolation=cv2.INTER_CUBIC)
        roi_risezed = cv2.resize(roi, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        gray_roi = cv2.cvtColor(roi_risezed, cv2.COLOR_BGR2GRAY)   
        _, binary_roi = cv2.threshold(gray_roi, 70, 255, cv2.THRESH_BINARY)
        blur_roi = cv2.GaussianBlur(binary_roi, (5, 5), 0)
        return blur_roi

    # função para o tesseract achar a string
    def _ocrImagePlate(self, roi):
        saida = ''
        if roi is not None:
            roi_resized = cv2.resize(roi, (800, 400))
            # cv2.imshow('roi', roi_resized)
            # configuração de caracteres que o pytessetact irá analisar
            config = r'-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 --psm 6'
            # imagem a ser analisada as letras,a linguagem e a configuração passada acima
            try:
                saida = pytesseract.image_to_string(roi_resized, lang='eng', config=config)
            except pytesseract.pytesseract.TesseractNotFoundError:
                with open(log_cloud, 'w') as log:
                    sys.stdout = log
                    print("Tesseract não encontrado. Certifique-se de que o Tesseract está instalado no ambiente.")
                return saida

            saida = saida.strip().upper()   
        return saida

# função que abre a canela e faz outras coisas relacionadas a sua abertura
def abertura_cancela():
    # Seção de código para o deploy
    with open(log_cloud, 'w') as log:
        sys.stdout = log
        print('concluido')
    # instância a classe imagem para a procura da placa
    imagem = Imagem()
    frame = imagem._ImageCapture()
    if frame is None:
        pass
    else:
        while frame is not None:
            frame = imagem._ImageCapture()
            roi = imagem._contorno_imagem(frame)
            img_preprocessada = imagem._preProcessamentoRoi(roi)
            saida = imagem._ocrImagePlate(img_preprocessada)
            with open(log_cloud, 'w') as log:
                sys.stdout = log
                print(saida)

            # instância classe database com os valores do banco a utilizar
            db = Database
            db._host = '162.240.34.167' 
            db._user = 'devbr_wp_kqeph'
            db._password = '#rbwqU77X3Zy5Zz#'
            db._database = 'devbr_wp_yx08y'
            # conecta a ele e gera um cursor para manipulação
            connection = db._connect()
            cursor = connection.cursor()
            # consulta do banco de dados em SQL
            cursor.execute(f"select placa_automovel from pessoas where placa_automovel = '{saida}';")
            placa = cursor.fetchall()

            if len(placa) > 0:
                placa = placa[0][0]
                placa = placa.strip().upper()

            if saida == placa:
                with open(log_cloud, 'w') as log:
                    sys.stdout = log
                    print('foi!!!!!!!!!!!!!')
                # arduino.write(b'0')
                time.sleep(5)         # os 2 comentados  pois só funcionam localmente
                # arduino.write(b'1')
                # armazena a data e dia
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # gera um log
                log_message = (f'{timestamp} - Cancela aberta - Placa {placa}')
                # executa um código pro banco adicionar esse log na tabela logs
                cursor.execute(f'insert into logs values(default, "{log_message}")')
                # comete a ação e fecha a conexão
                connection.commit()
                connection.close()
            
            else:
                # arduino.write(b'1')
                with open(log_cloud, 'w') as log:
                    sys.stdout = log
                    print(saida)

if __name__ == '__main__':
    # chama a função que executa tudo
    abertura_cancela()
