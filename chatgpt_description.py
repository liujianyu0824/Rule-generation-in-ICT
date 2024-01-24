import json
import time

import openai
import re
import logging
import random
from tqdm import tqdm
import jieba

openai.api_key = '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'

logging.basicConfig(
    filename='C:\\Users\\86183\\Desktop\\huawei_project\\logs\\chatgpt_description.log',
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S',
    level=logging.INFO)
logger = logging.getLogger(__name__)

data_file = 'C:\\Users\\86183\\Desktop\\huawei_project\\data\\description_test.json'

with open(data_file, 'r', encoding='utf-8') as f:
    original_data = json.load(f)

# 定义需要过滤的前缀和后缀停用词
pre_stop_words = ["如果", "导致", "将", "会", "需要", "可以", "当","可", "总是", "若", "是", "导致", "才"]
post_stop_words = ["时", "后", "下"]

def find_missing_substring(a, b):  # a:filter_text  b:origin_text
    i, j = 0, 0
    missing_substrings = []

    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            i += 1
            j += 1
        else:
            substring = ""
            while j < len(b) and a[i] != b[j]:
                substring += b[j]
                j += 1
            missing_substrings.append(substring)

    # 如果 b 还有剩余字符，将其全部添加到缺失的子字符串中
    if j < len(b):
        missing_substrings.append(b[j:])

    return missing_substrings

def del_stop(text):
    if text[0] in pre_stop_words:
        text = text[1:]
    if text[len(text)-1] in post_stop_words:
        text = text[:-1]
    # 使用jieba进行中文分词
    words = jieba.lcut(text)
    # 过滤前缀和后缀停用词
    if words[0] in pre_stop_words:
        words.pop(0)
    if words[len(words)-1] in post_stop_words:
        words.pop(len(words)-1)

    # 重新构建文本
    filtered_text = ''.join(words)

    return filtered_text

# 将LLM生成的文本转换为dict
def text_processed(text):
    pattern1 = r'"Subject":\s*"([^"]+)"[\s\S]*?'
    pattern2 = r'Condition":\s*"([^"]+)"[\s\S]*?'
    pattern3 = r'"Action":\s*"([^"]+)"[\s\S]*?'
    try:
        subject = re.search(pattern1, text).group(1)
        subject = del_stop(subject)
    except:
        subject = ''
    try:
        trigger = re.search(pattern2, text).group(1)
        if trigger[:len(subject)] == subject:
            trigger = trigger[len(subject):]
        trigger = del_stop(trigger)
    except:
        trigger = ''
    try:
        action = re.search(pattern3, text).group(1)
        if action[:len(subject)] == subject:
            action = action[len(subject):]
        action = del_stop(action)
    except:
        action = ''
    factor_dict = {
        "Subject": subject,
        "Trigger_condition": trigger,
        "Action": action
    }
    return factor_dict

#计算Precision、Recall、F1
def calculate_precision_recall(predicted_spans, true_spans):
    true_positive = len(set(predicted_spans) & set(true_spans))
    false_positive = len(predicted_spans) - true_positive
    false_negative = len(true_spans) - true_positive

    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
    if precision + recall == 0:
        f1 = 0
    else:
        f1 = 2 * (precision * recall) / (precision + recall)
    return precision, recall,f1


subject_count = 0
trigger_count = 0
action_count = 0
correct_num = [subject_count, trigger_count, action_count]

subject_subset = 0
trigger_subset = 0
action_subset = 0
correct_subset = [subject_subset, trigger_subset, action_subset]

subject_superset = 0
trigger_superset = 0
action_superset = 0
correct_superset = [subject_superset, trigger_superset, action_superset]


predicted_spans = {
    'subject_span': [],
    'trigger_span': [],
    'action_span': []
}

true_spans = {
    'subject_span': [],
    'trigger_span': [],
    'action_span': []
}
with tqdm(total=len(original_data)) as pbar:
    for data in original_data:
        pbar.update(1)
        input_text = data['sentence']
        if "**" in input_text:
            input_text = input_text.replace("*", "_")
        if len(data['rule_list'][1]['variable_description']) != 1:
            continue
        # input_text = '配置关闭MAC地址学习功能后，设备将不会再从该接口学习新的MAC地址，但是无法做到阻止某些设备或终端访问网络。'
        output_text = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user",
                 "content": str('''
你的任务是从一段文本中抽取出结构化的要素信息，抽取的结果必须从给定输入文本中抽取，与原文保持一致，不得更改表述。所抽取的文本中带有一段形如"如果xxxx，那么xx将xxxxx。"模式的描述，即"如果（trigger condition），（subject）将（action）"
以下是要素信息抽取的相关示例:
1、输入:"收到的分片报文数超过规格，请合理调整对端设备的MTU值。"
输出:
{"Subject":"对端设备"，
"Trigger Condition":"收到的分片报文数超过规格"，
"Action":"合理调整对端设备的MTU值"，
}
2、输入:"配置该命令时， link-number2 必须大于 link-number1 。"
输出:
{"Subject":"命令"，
"Trigger Condition":"配置该命令时"，
"Action":" link-number2 必须大于 link-number1 "，
}
3、输入:"去使能IP报文检查功能，会导致基于IP子网划分的VLAN、基于策略划分的VLAN和IPv6 over IPv4隧道功能不生效，使用前请确认。"
输出:
{"Subject":"基于IP子网划分的VLAN、基于策略划分的VLAN和IPv6 over IPv4隧道功能"，
"Trigger Condition":"去使能IP报文检查功能"，
"Action":"不生效"，
}
请仿照上面示例，从输入文本"''') + input_text + str('''"中抽取要素信息填充json:
{"Subject":""，
"Trigger Condition":""，
"Action":""，
}
其中Subject指规则的作用对象或被约束的实体，通常是文本中提及的一个具体事物或概念，TriggerCondition是规则中触发规则执行或生效的条件；Action是规则中规定的对主体的操作或行为。
抽取的结果应尽量简短简洁，且必须与原文表述一致
''')},
            ]
        )
        time.sleep(random.randint(20,24))
        logger.info("***********Input************")
        logger.info(data)
        logger.info("*********Result*********")
        logger.info(output_text['choices'][0]['message']['content'])
        logger.info("****************************")
        target_factor = text_processed(output_text['choices'][0]['message']['content'])

        try:
            subject = re.search(target_factor['Subject'], input_text)
            subject_pos = subject.span()
        except:
            subject_pos = (-1, -1)
        predicted_spans['subject_span'].append(subject_pos)
        true_spans['subject_span'].append((data['rule_list'][0]['span'][0],data['rule_list'][0]['span'][1]))

        try:
            trigger = re.search(target_factor['Trigger_condition'], input_text)
            trigger_pos = trigger.span()
        except:
            try:
                missing_substrings = find_missing_substring(target_factor['Trigger_condition'], input_text)
                print(target_factor['Trigger_condition'])
                for missing_substring in missing_substrings:
                    if missing_substring == target_factor['Subject']:
                        match = re.search(missing_substring, input_text)
                        start_index, end_index = match.span()
                        filter_text = filter_text[0:start_index] + target_factor['Subject'] + filter_text[start_index:]
                trigger = re.search(filter_text, input_text)
                trigger_pos = trigger.span()
            except:
                trigger_pos = (-1, -1)

        # 正则匹配
        pattern = "缺省情况"
        match = re.search(pattern, input_text)

        if match:
            trigger_pos = match.span()

        predicted_spans['trigger_span'].append(trigger_pos)
        true_spans['trigger_span'].append((data['rule_list'][1]['span'][0][0], data['rule_list'][1]['span'][0][1]))

        try:
            action = re.search(target_factor['Action'], input_text)
            action_pos = action.span()
        except:
            try:
                missing_substrings = find_missing_substring(target_factor['Action'], input_text)
                print(target_factor['Action'])
                for missing_substring in missing_substrings:
                    if missing_substring == target_factor['Subject']:
                        match = re.search(missing_substring, input_text)
                        start_index, end_index = match.span()
                        filter_text = filter_text[0:start_index] + target_factor['Subject'] + filter_text[start_index:]
                action = re.search(filter_text, input_text)
                action_pos = action.span()
            except:
                action_pos = (-1, -1)
        predicted_spans['action_span'].append(action_pos)
        true_spans['action_span'].append((data['rule_list'][2]['span'][0], data['rule_list'][2]['span'][1]))

        logger.info("*********Position*********")
        logger.info("Subject:" + str(subject_pos) + "  " + str(data['rule_list'][0]['span']))
        logger.info("Trigger:" + str(trigger_pos) + "  " + str(data['rule_list'][1]['span']))
        logger.info("Action:" + str(action_pos) + "  " + str(data['rule_list'][2]['span']))
        logger.info("****************************")

        # 统计指标
        factor_pos = [subject_pos, trigger_pos, action_pos]
        i = 0
        for pos in factor_pos:
            if i == 1:  #Variable_description单独处理
                if pos[0] == data["rule_list"][i]['span'][0][0] and pos[1] == data["rule_list"][i]['span'][0][1]:
                    correct_num[i] = correct_num[i] + 1
                elif pos[0] >= data["rule_list"][i]['span'][0][0] and pos[1] <= data["rule_list"][i]['span'][0][1]:
                    correct_subset[i] = correct_subset[i] + 1
                elif pos[0] <= data["rule_list"][i]['span'][0][0] and pos[1] >= data["rule_list"][i]['span'][0][1]:
                    correct_superset[i] = correct_superset[i] + 1
            else:
                if pos[0] == data["rule_list"][i]['span'][0] and pos[1] == data["rule_list"][i]['span'][1]:
                    correct_num[i] = correct_num[i] + 1
                elif pos[0] >= data["rule_list"][i]['span'][0] and pos[1] <= data["rule_list"][i]['span'][1]:
                    correct_subset[i] = correct_subset[i] + 1
                elif pos[0] <= data["rule_list"][i]['span'][0] and pos[1] >= data["rule_list"][i]['span'][1]:
                    correct_superset[i] = correct_superset[i] + 1
            i = i + 1
        print(correct_num,correct_subset,correct_superset)

subject_precision, subject_recall, subject_f1 = calculate_precision_recall(predicted_spans['subject_span'],
                                                                           true_spans['subject_span'])
print("Subject:  Precision {} Recall {} F1 {} ".format(subject_precision,subject_recall,subject_f1))
trigger_precision, trigger_recall, trigger_f1 = calculate_precision_recall(predicted_spans['trigger_span'],
                                                                           true_spans['trigger_span'])
print("Variable:  Precision {} Recall {} F1 {} ".format(trigger_precision, trigger_recall, trigger_f1))
action_precision, action_recall, action_f1 = calculate_precision_recall(predicted_spans['action_span'],
                                                                           true_spans['action_span'])
print("Action:  Precision {} Recall {} F1 {} ".format(action_precision, action_recall, action_f1))


print("ACC:")
for i in range(3):
    print(correct_num[i] / 144)

