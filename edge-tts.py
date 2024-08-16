import logging
import os
import re
import sys

from flask import Flask, request
from flask_cors import CORS
from qcloud_cos import CosConfig, CosS3Client


app = Flask(__name__, static_folder='tts')  # 指定静态文件夹
CORS(app)  # 这样设置允许所有来源的请求


#上传到COS
def uploadCos(file_path,relativePath):
    # 腾讯云COSV5Python SDK, 目前可以支持Python2.6与Python2.7以及Python3.x
    # pip安装指南:pip install -U cos-python-sdk-v5
    # cos最新可用地域,参照https://www.qcloud.com/document/product/436/6224
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    # 设置用户属性, 包括 secret_id, secret_key, region等。Appid 已在CosConfig中移除，请在参数 Bucket 中带上 Appid。Bucket 由 BucketName-Appid 组成
    region = ''      # 替换为用户的 region，已创建桶归属的region可以在控制台查看，https://console.cloud.tencent.com/cos5/bucket
    secret_id = ''     # 替换为用户的 SecretId，请登录访问管理控制台进行查看和管理，https://console.cloud.tencent.com/cam/capi
    secret_key = ''   # 替换为用户的 SecretKey，请登录访问管理控制台进行查看和管理，https://console.cloud.tencent.com/cam/capi
    bucket_name = ''

    # COS支持的所有region列表参见https://www.qcloud.com/document/product/436/6224
    token = None               # 如果使用永久密钥不需要填入token，如果使用临时密钥需要填入，临时密钥生成和使用指引参见https://cloud.tencent.com/document/product/436/14048
    domain = None # domain可以不填，此时使用COS区域域名访问存储桶。domain也可以填写用户自定义域名，或者桶的全球加速域名
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Domain=domain)  # 获取配置对象
    client = CosS3Client(config)
    # 文件流 简单上传
    with open(f'./{relativePath}', 'rb') as fp:
        response = client.put_object(
            Bucket=bucket_name,
            Body=fp,
            Key=relativePath,
            StorageClass='STANDARD',
            ContentType='audio/mpeg'
        )
        print(response['ETag'])
    # 上传完成之后删除文件
    os.remove(file_path)  # 删除文件

    # 构建文件的访问 URL
    url = f"https://{bucket_name}.cos.{region}.myqcloud.com{relativePath}"
    print("文件访问路径:", url)
    return url

voiceMap = {
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",
    "xiaoyi": "zh-CN-XiaoyiNeural",
    "yunjian": "zh-CN-YunjianNeural",
    "yunxi": "zh-CN-YunxiNeural",
    "yunxia": "zh-CN-YunxiaNeural",
    "yunyang": "zh-CN-YunyangNeural",
    "xiaobei": "zh-CN-liaoning-XiaobeiNeural",
    "xiaoni": "zh-CN-shaanxi-XiaoniNeural",
    "hiugaai": "zh-HK-HiuGaaiNeural",
    "hiumaan": "zh-HK-HiuMaanNeural",
    "wanlung": "zh-HK-WanLungNeural",
    "hsiaochen": "zh-TW-HsiaoChenNeural",
    "hsioayu": "zh-TW-HsiaoYuNeural",
    "yunjhe": "zh-TW-YunJheNeural",
}


def getVoiceById(voiceId):
    return voiceMap.get(voiceId)


# 删除html标签
def remove_html(string):
    regex = re.compile(r'<[^>]+>')
    return regex.sub('', string)


def createAudio(text, file_name, voiceId):
    new_text = remove_html(text)
    print(f"Text without html tags: {new_text}")
    voice = getVoiceById(voiceId)
    if not voice:
        return "error params"

    pwdPath = os.getcwd()
    #本地路径
    filePath = pwdPath + "/tts/" + file_name
    #相对路径
    relativePath = "/tts/" + file_name
    dirPath = os.path.dirname(filePath)
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)
    if not os.path.exists(filePath):
        # 用open创建文件 兼容mac
        open(filePath, 'a').close()

    script = 'edge-tts --voice ' + voice + ' --text "' + new_text + '" --write-media ' + filePath
    os.system(script)
    #这里可以选择上传云存储和本地使用
    # 上传到腾讯云COS云存储-返回云存储地址
#     url = uploadCos(filePath, relativePath)

    # 音频保存到本地-直接返回音频地址
    url = f'http://127.0.0.1:2020/{relativePath}'
    return url


def getParameter(paramName):
    if request.args.__contains__(paramName):
        return request.args[paramName]
    return ""

@app.route('/dealAudio',methods=['POST','GET'])
def dealAudio():
    text = getParameter('text')
    file_name = getParameter('file_name')
    voice = getParameter('voice')
    return createAudio(text, file_name, voice)

# 添加一个路由来处理静态文件的请求
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)


@app.route('/')
def index():
    return 'welcome to my tts!'

if __name__ == "__main__":
    app.run(port=2020,host="127.0.0.1",debug=True)
