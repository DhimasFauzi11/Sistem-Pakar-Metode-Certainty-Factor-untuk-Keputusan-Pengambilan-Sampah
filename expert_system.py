# expert_system.py

expert_system_config = {
    "metadata": {
        "name": "Sistem Pakar Pengangkutan Sampah Parakan Ceuri",
        "version": "3.2 (Final Table Data)",
        "description": "Konfigurasi Data berdasarkan Notulensi Wisata Budaya"
    },
    "global_fusion_weights": {
        "cf_fuzzy_1_internal": 0.7,
        "cf_fuzzy_2_external": 0.9
    },
    "fuzzy_1_internal": {
        "description": "Fuzzy 1 (Kondisi tong sampah)",
        "total_expert_weight_sum": 1.8,
        "attributes": [
            {
                "id": "kepenuhan",
                "name": "Kepenuhan",
                "cf_pakar": 0.9,
                "rules": [
                    {"label": "Kosong", "range": "< 40%", "cf_output": 0.3},
                    {"label": "Sedang", "range": "40% - 70%", "cf_output": 0.6},
                    {"label": "Penuh", "range": "> 70%", "cf_output": 0.9}
                ]
            },
            {
                "id": "kebusukan",
                "name": "Kebusukan",
                "cf_pakar": 0.5,
                "rules": [
                    {"label": "Rendah", "range": "< 110 ppm", "cf_output": 0.3},
                    {"label": "Sedang", "range": "110 - 190 ppm", "cf_output": 0.6},
                    {"label": "Tinggi", "range": "> 190 ppm", "cf_output": 0.9}
                ]
            },
            {
                "id": "kategori_sampah",
                "name": "Kategori Sampah",
                "cf_pakar": 0.4,
                "rules": [
                    {"label": "Organik", "value": "organic", "cf_output": 0.2},
                    {"label": "Non-Organik", "value": "anorganic", "cf_output": 0.9}
                ]
            }
        ]
    },
    "fuzzy_2_external": {
        "description": "Fuzzy 2 (Kondisi Lingkungan)",
        "total_expert_weight_sum": 2.9,
        "attributes": [
            {
                "id": "suhu",
                "name": "Suhu",
                "cf_pakar": 0.3,
                "rules": [
                    {"label": "Rendah", "range": "< 25", "cf_output": 0.3},
                    {"label": "Sedang", "range": "25 - 30", "cf_output": 0.6},
                    {"label": "Tinggi", "range": "> 30", "cf_output": 0.9}
                ]
            },
            {
                "id": "kelembaban",
                "name": "Kelembaban",
                "cf_pakar": 0.6,
                "rules": [
                    {"label": "Rendah", "range": "< 40%", "cf_output": 0.3},
                    {"label": "Sedang", "range": "40 - 70%", "cf_output": 0.6},
                    {"label": "Tinggi", "range": "> 70%", "cf_output": 0.9}
                ]
            },
            {
                "id": "event",
                "name": "Event",
                "cf_pakar": 1.0,
                "rules": [
                    {"label": "Tidak Ada", "value": False, "cf_output": 0.2},
                    {"label": "Ada", "value": True, "cf_output": 0.9}
                ]
            },
            {
                "id": "lokasi",
                "name": "Lokasi",
                "cf_pakar": 0.6,
                "rules": [
                    {"label": "Biasa", "value": "biasa", "cf_output": 0.3},
                    {"label": "Strategis", "value": "strategis", "cf_output": 0.9}
                ]
            },
            {
                "id": "laju",
                "name": "Laju",
                "cf_pakar": 0.4,
                "rules": [
                    {"label": "Lambat", "range": "< 30%", "cf_output": 0.4},
                    {"label": "Cepat", "range": "> 30%", "cf_output": 0.8}
                ]
            }
        ]
    }
}
