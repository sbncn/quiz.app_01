# 1. Python'un en güncel slim versiyonunu kullan
FROM python:3.11-slim

# 2. Çalışma dizinini ayarla
WORKDIR /app

# 3. Proje dosyalarını container içine kopyala
COPY . .

# 4. Gerekli bağımlılıkları yükle
RUN pip install --no-cache-dir -r requirements.txt

# 5. Uygulamayı başlatmak için komut
CMD ["python", "main.py"]

#FROM moby/buildkit:buildx-stable-1

# Paketleri güncelle
#RUN apt-get update && apt-get upgrade -y