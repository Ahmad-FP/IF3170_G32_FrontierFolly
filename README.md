# IF3170_G32_FrontierFolly — Tugas Besar 1: Searching

Repositori Tugas Besar 1 **IF3170 Inteligensi Artifisial 2026/2027**, kelompok **G32 FrontierFolly**.

Program menyelesaikan permasalahan *3D packing* pada peti kemas truk: menyusun paket ke dalam truk berukuran 10 × 20 × 5 agar total value paket yang termuat maksimum, dengan kendala batas peti kemas, tabrakan antar paket, kapasitas berat (500), larangan paket melayang (wajib ditopang), dan larangan penumpukan barang pecah-belah (*fragile*). Solusi dicari dengan algoritma local search: empat varian Hill Climbing, Simulated Annealing, dan Genetic Algorithm, plus objective alternatif *urgency* sebagai bonus.

## Struktur Repositori

```
.
├── docs/        # laporan (PDF) + sumber DOCX
├── output/      # hasil run algoritma (state JSON, plot PNG, ringkasan JSON)
└── src/
    ├── constraint.py         # validasi constraint state
    ├── initial_state.py      # generator initial state acak
    ├── visual.py             # visualisasi state 3D dan kurva nilai objective
    ├── data/                 # data paket & truk
    ├── hill_climbing/        # 4 varian hill climbing + eksperimen
    ├── simulated_annealing/  # simulated annealing + eksperimen
    └── genetic-algorithm/    # genetic algorithm
```

## Setup

Dibutuhkan Python 3.10+ dan matplotlib:

```bash
python -m pip install -r requirements.txt
```

Untuk menjalankan notebook eksperimen, tambahan Jupyter:

```bash
python -m pip install jupyter
```

## Cara Menjalankan

Perintah dijalankan dari masing-masing folder di dalam `src/` karena program membaca data dari folder `../data`.

| Bagian | Perintah |
|---|---|
| Hill Climbing (4 varian × 3 run) | `cd src/hill_climbing && python hill_climbing.py` |
| Notebook eksperimen HC (+ bonus urgency) | `cd src/hill_climbing && jupyter notebook main.ipynb` |
| Simulated Annealing | `cd src/simulated_annealing && python sa.py` |
| Genetic Algorithm | `cd src/genetic-algorithm && jupyter notebook main.ipynb` |
| Uji constraint | `cd src/hill_climbing && python ../test_constraint.py` |
| Uji initial state | `cd src && python test_initial_state.py` |
| Uji hill climbing | `cd src/hill_climbing && python test_hill_climbing.py` |

Hasil run ditulis ke `output/` (state `.json`, gambar `.png`, dan ringkasan `.json` per varian/run).

## Hasil Eksperimen (3 run)

| Algoritma | Nilai akhir terbaik |
|---|---|
| Steepest ascent | 2140 |
| Stochastic | 1710 |
| Sideways move | 2140 |
| Random restart | 2250 |
| Simulated annealing | 2040 |

Ringkasan HC ada di `output/hill_climbing/summary.json`, SA di `output/simulated_annealing/run*/result.json`. Analisis lengkap ada di laporan.

## Pembagian Tugas

| Anggota | NIM | Kontribusi |
|---|---|---|
| Mohammad Najmutstsaqib | 13223040 | Inisialisasi pemodelan 3D packing dan generator initial state, validasi constraint dasar, serta pengembangan Genetic Algorithm beserta eksperimennya. |
| Ega Luthfi Rais | 13524115 | Implementasi empat varian Hill Climbing dan heuristik penempatan paket, eksekusi dan visualisasi eksperimen Hill Climbing (tiga run per varian), bonus objective alternatif (urgency), penyusunan bab Pembahasan dan analisis laporan. |
| Ahmad Fauzan Putra | 13524141 | Implementasi Simulated Annealing, fungsi visualisasi umum (state 3D dan kurva nilai), README dan struktur awal repositori, dukungan eksperimen Simulated Annealing. |

## Laporan

Laporan lengkap tersedia di [`docs/`](docs/) (PDF + sumber DOCX).
