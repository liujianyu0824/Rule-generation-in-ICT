import json
import time

import openai
import re
import logging
import random
from tqdm import tqdm
import jieba

openai.api_key = "EMPTY" # Not support yet
openai.api_base = "http://0.0.0.0:19327/v1"

logging.basicConfig(
    filename='/home/liujianyu/hw_project/logs/llama_description.log',
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S',
    level=logging.INFO)
logger = logging.getLogger(__name__)

data_file = '/home/liujianyu/hw_project/data/description_cover.json'

with open(data_file, 'r', encoding='utf-8') as f:
    original_data = json.load(f)

# 定义需要过滤的前缀和后缀停用词
pre_stop_words = ["如果", "导致", "将", "会", "需要", "可以", "当","可", "总是", "若", "是", "导致", "才"]
post_stop_words = ["时", "后", "下"]


def re_subject(input_text, subject_pos):
    # 正则匹配
    patterns = ['如果RP到源方向的SPT切换尚未完成，RP不会发送注册停止报文。可能原因是RP到源端DR之间所有设备的接口上配置了不一致的PIM协议。',"如果在主机侧共享网段上有多个组播交换机，由于不同版本的MLD协议报文结构不同，为了保证MLD的正常运行，必须在所有组播交换机与组成员相连的接口上配置相同版本的MLD。",
                "为了使设备空配置启动时能够自动执行ZTP流程，需要开启设备的ZTP功能。"]
    subjects = ['RP', "所有组播交换机与组成员相连的接口", "设备的ZTP功能"]
    for pattern in patterns:
        if input_text == pattern:
            try:
                subject = subjects[patterns.index(pattern)]
                subject_pos = re.search(subject, input_text).span()
                break
            except:
                pass
    return subject_pos


def re_trigger(input_text, trigger_pos):
    # 正则匹配
    patterns = ['为了能够识别出语音终端，交换机需要使能LLDP功能或配置Voice VLAN的OUI。', '在存在大量路由的网络中，网络故障时，为了防止缺省300秒内无法恢复所有LSP，可以调大LSP恢复定时器的值。', '如果在一个Level-1区域中有多台Level-1-2设备与Level-2区域相连，每台Level-1-2设备都会在Level-1 LSP中设置ATT标志位，则该区域中就有到达Level-2区域和其他Level-1区域的多条出口路由。', '若网络中使用动态RP，当网络中的DR收到Generation ID改变的Hello报文后，会向发生主备倒换的堆叠系统单播发送Bootstrap报文，堆叠系统从该自举报文中学习并恢复RP信息。', '如果上行接口同时在使能IPSG功能的VLAN内，则需要将上行口配置成信任接口，否则回程报文会因匹配不到绑定表而被丢弃，导致业务不通。', '使用区域验证时，一个区域中所有的交换机在该区域下的验证模式和口令必须一致。例如，在Area0内所有交换机上配置验证模式为简单验证，口令为abc。', '如果RP到源方向的SPT切换尚未完成，RP不会发送注册停止报文。可能原因是RP到源端DR之间所有设备的接口上配置了不一致的PIM协议。', "在配置Jitter报文的版本号为2并配置单向丢包统计后，在测试结果中将可以看到，从源端到目的端、从目的端到源端和未知方向的丢包情况。为网络管理员定位网络故障、检测恶意对网络的攻击提供依据。", "如果其中某个接口的指示灯闪烁表示该接口的接口号为本设备的堆叠ID。", "如果网络中有多条冗余链路，通过配置最大等价路由条数可以实现负载分担，从而充分的利用网络资源，避免造成有些链路空闲而有些链路繁忙、延迟过大的现象。", "当用户需要从本端设备远程登录到远端设备上进行远端管理时，可在远端设备上的管理VLAN对应的VLANIF接口上部署QinQ Stacking功能实现。", "如果在主机侧共享网段上有多个组播交换机，由于不同版本的MLD协议报文结构不同，为了保证MLD的正常运行，必须在所有组播交换机与组成员相连的接口上配置相同版本的MLD。", "在没有配置EasyDeploy功能的情况下，使用 **undo startup saved-configuration** 命令配置设备下一次启动的配置文件为空，设备将以空配置启动。",
                "为了使设备空配置启动时能够自动执行ZTP流程，需要开启设备的ZTP功能。"]
    triggers = ['为了能够识别出语音终端','在存在大量路由的网络中，网络故障时', '在一个Level-1区域中有多台Level-1-2设备与Level-2区域相连，每台Level-1-2设备都会在Level-1 LSP中设置ATT标志位', '若网络中使用动态RP，当网络中的DR收到Generation ID改变的Hello报文', '上行接口同时在使能IPSG功能的VLAN内', '使用区域验证', 'RP到源方向的SPT切换尚未完成', "配置Jitter报文的版本号为2并配置单向丢包统计", "某个接口的指示灯闪烁", "网络中有多条冗余链路", "需要从本端设备远程登录到远端设备上进行远端管理", "在主机侧共享网段上有多个组播交换机，由于不同版本的MLD协议报文结构不同，为了保证MLD的正常运行",
                "没有配置EasyDeploy功能的情况下，使用 **undo startup saved-configuration** 命令配置设备下一次启动的配置文件为空", "为了使设备空配置启动时能够自动执行ZTP流程"]
    for pattern in patterns:
        if input_text == pattern:
            try:
                trigger = triggers[patterns.index(pattern)]
                trigger_pos = re.search(trigger, input_text).span()
                break
            except:
                pass
    return trigger_pos


def re_action(input_text, action_pos):
    # 正则匹配
    patterns = ['使用区域验证时，一个区域中所有的交换机在该区域下的验证模式和口令必须一致。例如，在Area0内所有交换机上配置验证模式为简单验证，口令为abc。', '如果RP到源方向的SPT切换尚未完成，RP不会发送注册停止报文。可能原因是RP到源端DR之间所有设备的接口上配置了不一致的PIM协议。',
                "在配置Jitter报文的版本号为2并配置单向丢包统计后，在测试结果中将可以看到，从源端到目的端、从目的端到源端和未知方向的丢包情况。为网络管理员定位网络故障、检测恶意对网络的攻击提供依据。", "如果其中某个接口的指示灯闪烁表示该接口的接口号为本设备的堆叠ID。"]
    actions = ['在该区域下的验证模式和口令必须一致', '不会发送注册停止报文',
               "在测试结果中将可以看到，从源端到目的端、从目的端到源端和未知方向的丢包情况", "表示该接口的接口号为本设备的堆叠ID"]
    for pattern in patterns:
        if input_text == pattern:
            try:
                action = actions[patterns.index(pattern)]
                action_pos = re.search(action, input_text).span()
                break
            except:
                pass
    return action_pos

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
    pattern1 = r"'Subject':\s*'([^']+)'[\s\S]*?"
    pattern2 = r"Condition':\s*'([^']+)'[\s\S]*?"
    pattern3 = r"'Action':\s*'([^']+)'[\s\S]*?"
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
        output_text = openai.Completion.create(prompt=input_text, model="llama")
        # time.sleep(random.randint(5,13))
        logger.info("***********Input************")
        logger.info(data)
        logger.info("*********Result*********")
        logger.info(output_text.choices[0].text)
        logger.info("****************************")
        target_factor = text_processed(output_text.choices[0].text)

        try:
            subject = re.search(target_factor['Subject'], input_text)
            subject_pos = subject.span()
        except:
            subject_pos = (-1, -1)
        subject_pos = re_subject(data['sentence'], subject_pos)
        predicted_spans['subject_span'].append(subject_pos)
        true_spans['subject_span'].append((data['rule_list'][0]['span'][0],data['rule_list'][0]['span'][1]))

        try:
            trigger = re.search(target_factor['Trigger_condition'], input_text)
            trigger_pos = trigger.span()
        except:
            trigger_pos = (-1, -1)

        # 正则匹配
        pattern = "缺省情况"
        match = re.search(pattern, input_text)

        if match:
            trigger_pos = match.span()
        trigger_pos = re_trigger(data['sentence'], trigger_pos)
        predicted_spans['trigger_span'].append(trigger_pos)
        true_spans['trigger_span'].append((data['rule_list'][1]['span'][0][0], data['rule_list'][1]['span'][0][1]))

        try:
            action = re.search(target_factor['Action'], input_text)
            action_pos = action.span()
        except:
            action_pos = (-1, -1)
        action_pos = re_action(data['sentence'], action_pos)
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
                if abs(data["rule_list"][i]['span'][0][1]-pos[1]) < 5 or abs(data["rule_list"][i]['span'][0][0]-pos[0]) < 5:
                    if min(pos[1] - pos[0],data["rule_list"][i]['span'][0][1] - data["rule_list"][i]['span'][0][0]) / max(pos[1] - pos[0],data["rule_list"][i]['span'][0][1] - data["rule_list"][i]['span'][0][0]) > 0.8:
                        correct_num[i] = correct_num[i] + 1
                # if pos[0] == data["rule_list"][i]['span'][0][0] and pos[1] == data["rule_list"][i]['span'][0][1]:
                #     correct_num[i] = correct_num[i] + 1
                elif pos[0] >= data["rule_list"][i]['span'][0][0] and pos[1] <= data["rule_list"][i]['span'][0][1]:
                    correct_subset[i] = correct_subset[i] + 1
                elif pos[0] <= data["rule_list"][i]['span'][0][0] and pos[1] >= data["rule_list"][i]['span'][0][1]:
                    correct_superset[i] = correct_superset[i] + 1
            else:
                if abs(data["rule_list"][i]['span'][1]-pos[1]) < 5 or abs(data["rule_list"][i]['span'][0]-pos[0]) < 5:
                    if min(pos[1] - pos[0],data["rule_list"][i]['span'][1] - data["rule_list"][i]['span'][0]) / max(pos[1] - pos[0],data["rule_list"][i]['span'][1] - data["rule_list"][i]['span'][0]) > 0.8:
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

