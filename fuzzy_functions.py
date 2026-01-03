# fuzzy_functions.py
from expert_system import expert_system_config

def calculate_fuzzy_1_internal(penuh, kebusukan, jenis):
    config = expert_system_config['fuzzy_1_internal']
    total_weight = config['total_expert_weight_sum']
    score_sum = 0

    for attr in config['attributes']:
        cf = attr['cf_pakar']
        val = None

        if attr['id'] == 'kepenuhan':
            val = penuh
        elif attr['id'] == 'kebusukan':
            val = kebusukan
        elif attr['id'] == 'kategori_sampah':
            val = jenis

        # hitung cf berdasarkan rules
        for rule in attr['rules']:
            if 'range' in rule:
                r = rule['range']
                if '<' in r and val < float(r.split('<')[1].replace('%','').replace(' ppm','')):
                    cf_output = rule['cf_output']
                    break
                elif '>' in r and val > float(r.split('>')[1].replace('%','').replace(' ppm','')):
                    cf_output = rule['cf_output']
                    break
                elif '-' in r:
                    low, high = r.split('-')
                    low = float(low.replace('%','').replace(' ppm',''))
                    high = float(high.replace('%','').replace(' ppm',''))
                    if low <= val <= high:
                        cf_output = rule['cf_output']
                        break
            else:
                if val == rule['value']:
                    cf_output = rule['cf_output']
                    break

        score_sum += cf * cf_output

    return score_sum / total_weight


def calculate_fuzzy_2_external(suhu, lembab, event_bool, lokasi, laju):
    config = expert_system_config['fuzzy_2_external']
    total_weight = config['total_expert_weight_sum']
    score_sum = 0

    for attr in config['attributes']:
        cf = attr['cf_pakar']
        val = None

        if attr['id'] == 'suhu':
            val = suhu
        elif attr['id'] == 'kelembaban':
            val = lembab
        elif attr['id'] == 'event':
            val = event_bool
        elif attr['id'] == 'lokasi':
            val = lokasi
        elif attr['id'] == 'laju':
            val = laju

        for rule in attr['rules']:
            if 'range' in rule:
                r = rule['range']
                if '<' in r and val < float(r.split('<')[1].replace('%','')):
                    cf_output = rule['cf_output']
                    break
                elif '>' in r and val > float(r.split('>')[1].replace('%','')):
                    cf_output = rule['cf_output']
                    break
                elif '-' in r:
                    low, high = r.split('-')
                    low = float(low.replace('%',''))
                    high = float(high.replace('%',''))
                    if low <= val <= high:
                        cf_output = rule['cf_output']
                        break
            else:
                if val == rule['value']:
                    cf_output = rule['cf_output']
                    break

        score_sum += cf * cf_output

    return score_sum / total_weight
