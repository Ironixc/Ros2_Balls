# Ros2_Balls

## Cara Menjalankan Project

1. Masuk ke folder `ros2_game`:
```bash
   cd ~/ros2_game

```

2. Build package yang ada di folder `camera_node__cpp`:
```bash
colcon build --packages-select camera_node__cpp

```


3. Ambil atau *source* package yang sudah kita build tadi:
```bash
source install/setup.bash

```


4. Jalankan publisher kamera agar nanti `game_node` bisa mengambil kamera asli:
```bash
ros2 run camera_node__cpp Camera_node

```


*(mengubah parameter langsung tanpa merubah kode : `ros2 run camera_node__cpp Camera_node --ros-args -p fps:=20.0 -p Lebar:=...`)*
5. Jalankan logika game dan deteksi kamera (untuk mendeteksi apakah objek itu tutup botol):
```bash
python3 src/camera_node__cpp/src/game_node.py

```


*(mengubah parameter langsung tanpa merubah kode : `python3 src/camera_node__cpp/src/game_node.py --ros-args -p balls:=2 -p ...`)*
6. melihat score di CMD/terminal (untuk mengecek apakah score-nya bertambah atau tidak), buka terminal baru dan jalankan:
```bash
ros2 topic echo /game/score

```



---

## Arsitektur

### Node

Ada 2 Node utama:

* `Camera_node.cpp`
* `game_node.py`

### Topic

* **`/camera/image_raw`**
* **Publisher:** `Camera_node.cpp` (mem-publish kamera asli)
* **Subscriber:** `game_node.py` (mengambil kamera asli)


* **`/game/debug_image`**
* **Publisher:** `game_node.py` (mem-publish kamera yang sudah ada deteksi YOLO-nya)


* **`/game/score`**
* **Publisher:** `game_node.py` (mem-publish score ketika score berubah)



### Parameter

```yaml
camera_node:
  ros__parameters:
    source: "0"   # Seharusnya buat bisa ganti source kayak mau kamera apa atau file mungkin, tapi idk lagi
    fps: 30.0     # ya gitu
    Lebar: 640    # ya gitu
    Tinggi: 480   # ya gitu

game_node:
  ros__parameters:
    balls: 3      # Jumlah bola
    holdd: 2.0    # Berapa lama object harus berada di dalam bola (detik)
    v: 150.0      # Kecepatan bola (gak ngaruh kan di kode di-random lagi)
    radius: 40    # Besar bola (gak ngaruh kan di kode di-random lagi)
    marea: 300    # Minimum area agar dianggap sebagai object
    timer: 60.0   # Timer game, jika melebihi 60 detik ini maka game over (cuman belum bikin cara gimana ngulangnya, nanti saja lah)

```

---

## Alasan Desain

Desainnya kepisah antara C++ (`Camera_node.cpp`) dan Python (`game_node.py`) kayak gini karena kalo semuanya C++ error di YOLO-nya, tapi alur node, topic, dan parameternya jalan sesuai tugas.

---

## Kendala

1. Kamera  nge-frame dan harus di-force pakai `CAP_V4L2` agar FPS-nya aman.
2. Awalnya nyoba pakai C++ semua tapi gak bisa karena model ONNX-nya gak mau ke-convert (padahal udah coba pakai library open source juga tetep gak mau), akhirnya node game dan deteksinya pindah pakai Python baru bisa jalan.
3. Kalau ada terlalu banyak object yang ke-detect di kamera atau jumlah bolanya diset kebanyakan, kameranya bakal nge-frame.
4. Deteksi YOLO-nya kadang masih salah ngedeteksi gambar/benda lain yang bukan tutup botol dan belum fix.

---

## Bonus

1. **Parameter Dinamis:** mengubah parameter di tengah-tengah saat program sedang berjalan :
```bash
ros2 param set /<nama_node> <nama_parameter> <nilai>

```

---

## Screenshot rqt_graph

![RQT Graph Screenshot](<Screenshot rqt_graph/Screenshot from 2026-10-28 20-37-43.png>)

---

## Video demo

---

<video src="Demo_Vidio/demo.mp4" controls="controls" width="600"></video>