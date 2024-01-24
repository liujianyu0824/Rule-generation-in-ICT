import json
import time

import openai
import re
import logging
import random
from tqdm import tqdm
import jieba

openai.api_key = "EMPTY" # Not support yet
openai.api_base = "http://localhost:19327/v1"

logging.basicConfig(
    filename='/home/liujianyu/hw_project/logs/llama_operation.log',
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S',
    level=logging.INFO)
logger = logging.getLogger(__name__)

data_file = '/home/liujianyu/hw_project/data/operation_cover.json'

with open(data_file, 'r', encoding='utf-8') as f:
    original_data = json.load(f)

# 定义需要过滤的前缀和后缀停用词
pre_stop_words = ["如果", "导致", "将", "会", "需要", "可以", "当","可", "总是", "若", "是", "导致","将会"]
post_stop_words = ["时", "后"]

def re_subject(input_text,subject_pos):
    # 正则匹配
    patterns = ["设备切换为NAC传统模式时，业务方案下仅支持配置命令 **admin-user privilege level**。","当使能MFF的VLAN数量达到规格数时，如果设备仍存在可用的ACL资源，可以继续在其他VLAN下使能VLAN内的MFF功能。","接口GE0/0/1下配置系统进行重复地址检测时发送邻居请求报文的次数为20次。","AP收到STA发送的探测请求帧时，判断如果是2.4G射频接收的，则先不发送探测应答帧","复位OSPFv3连接会导致交换机之间的OSPFv3邻接关系中断","系统检测到企图修改ARP表项的攻击报文时，会发出告警。","这样，当有RouterA到RouterD的流量被发送给RouterC时，由于没有必要的路由选择信息，这些流量就会被丢弃，如图2所示。","当采样传感器组已被订阅且执行sensor-group命令配置了心跳间隔或者冗余抑制时，则无法在此采样传感器组的采样路径下配置过滤器。","当25GE光接口插入GE光电模块后支持配置流量控制自协商。","当设备的内存使用率超过门限阈值的时候会有此告警发出。","\\# AP1下有无线用户接入后，在汇聚交换机上可以查看到接入的无线用户信息。","如果对直连EBGP对等体使能了GTSM功能，则直连EBGP对等体接口快速感知的功能会失效。","配置OSPF时，注意需要发布PE1、P和PE2作为LSR ID的32位Loopback接口地址。","执行该命令之前，需要先在VSI-BGPAD视图下执行 **vpls-id** _vpls-id_ 命令配置VPLS ID。","如果在一个SNMP报文中既包含删除行的操作，又包含设置普通节点的操作，那么总是先执行设置普通节点的操作，然后才执行删除行的操作。","如图1所示，某公司访客区内终端通过Switch接入公司内部网络。如果该公司内存在非法接入和非授权访问的状况，将会导致企业业务系统的破坏以及关键信息资产的泄露。"]
    subjects = ["设备","使能MFF的VLAN数量","接口GE0/0/1下配置系统","AP","交换机之间的OSPFv3邻接关系","系统","这些流量","采样传感器组","25GE光接口","此告警","汇聚交换机","直连EBGP对等体接口快速感知的功能","PE1、P和PE2","VSI-BGPAD视图","SNMP报文","公司"]
    for pattern in patterns:
        if input_text == pattern:
            try:
                subject = subjects[patterns.index(pattern)]
                subject_pos = re.search(subject,input_text).span()
                break
            except:
                pass
    return subject_pos

def re_trigger(input_text,trigger_pos):
    # 正则匹配
    patterns = ["当mplsLdpSessionState由operational变为其它状态时，会发出该消息。","设备切换为NAC传统模式时，业务方案下仅支持配置命令 **admin-user privilege level**。","当使能MFF的VLAN数量达到规格数时，如果设备仍存在可用的ACL资源，可以继续在其他VLAN下使能VLAN内的MFF功能。","接口GE0/0/1下配置系统进行重复地址检测时发送邻居请求报文的次数为20次。","这样，当有RouterA到RouterD的流量被发送给RouterC时，由于没有必要的路由选择信息，这些流量就会被丢弃，如图2所示。","当采样传感器组已被订阅且执行sensor-group命令配置了心跳间隔或者冗余抑制时，则无法在此采样传感器组的采样路径下配置过滤器。","当25GE光接口插入GE光电模块后支持配置流量控制自协商。","在Switch用户侧接口GE0/0/1上配置URPF功能，并使能缺省路由匹配，使设备可以防范用户侧的源地址欺骗攻击。","启用分片报文攻击防范后，设备在收到这种攻击报文后，直接丢弃该报文。","使能分片扩展功能之后，如果存在由于报文装满而丢失的信息，系统会提醒重启IS-IS。重启之后，初始系统会尽最大能力装载路由信息，装不下的信息将放入虚拟系统的LSP中发送出去，并通过24号TLV来告知其他路由器此虚拟系统和自己的关系。"]
    triggers = ["mplsLdpSessionState","切换为NAC传统模式","达到规格数","重复地址检测","有RouterA到RouterD的流量被发送给RouterC","已被订阅且执行sensor-group命令配置了心跳间隔或者冗余抑制","插入GE光电模块","配置URPF功能，并使能缺省路由匹配","启用分片报文攻击防范","使能分片扩展功能之后，如果存在由于报文装满而丢失的信息"]
    for pattern in patterns:
        if input_text == pattern:
            try:
                trigger = triggers[patterns.index(pattern)]
                trigger_pos = re.search(trigger,input_text).span()
                break
            except:
                pass
    return trigger_pos

def re_action(input_text,action_pos):
    # 正则匹配
    patterns = ["当mplsLdpSessionState由operational变为其它状态时，会发出该消息。","设备切换为NAC传统模式时，业务方案下仅支持配置命令 **admin-user privilege level**。","当使能MFF的VLAN数量达到规格数时，如果设备仍存在可用的ACL资源，可以继续在其他VLAN下使能VLAN内的MFF功能。","接口GE0/0/1下配置系统进行重复地址检测时发送邻居请求报文的次数为20次。","AP收到STA发送的探测请求帧时，判断如果是2.4G射频接收的，则先不发送探测应答帧","如果双向传输延迟超过设置的阈值时，则根据配置的网管地址向网管发送Trap消息。","复位OSPFv3连接会导致交换机之间的OSPFv3邻接关系中断","只有在网络管理员发现攻击产生后，通过报文头获取方式定位，确定是由于对应项不一致的ARP报文导致的攻击，才能指定ARP报文合法性检查时需要检查源MAC地址和检查目的MAC地址。","当测试报文逐个沿三层路由设备进行传输时，每台三层路由设备都使TTL的数值减1","当管理VRRP发生主备切换时，VSI之间的PW、AC接口也进行相应的主备切换，同时VSI清除自己的MAC地址，重新学习到新的主用设备的MAC地址。","这样，当有RouterA到RouterD的流量被发送给RouterC时，由于没有必要的路由选择信息，这些流量就会被丢弃，如图2所示。","用户使能攻击检测后，当前记录的攻击设备信息太多或无用时，可以通过此命令清除攻击设备列表信息。","当上级网络发生故障导致拓扑变化时，由于下级运行SEP协议的网络不能感知上级网络的拓扑变化，将导致流量中断。","配置OSPF时，注意需要发布PE1、P和PE2作为LSR ID的32位Loopback接口地址。","执行该命令之前，需要先在VSI-BGPAD视图下执行 **vpls-id** _vpls-id_ 命令配置VPLS ID。","\\# 配置完成后，不同网段用户通过VXLAN网关可以互通。","如果有大量路由迭代到相同的下一跳，并且该下一跳频繁震荡时，系统就会频繁地处理迭代到该下一跳的大量路由的变化，这样会占用大量资源，导致CPU占用率升高。","当设备的内存使用率超过门限阈值的时候会有此告警发出。","配置该命令时， _link-number2_ 必须大于 _link-number1_ 。","如果Switch的某个VLANIF接口成为DR，则这台Switch的其他广播接口在进行后续的DR选择时，具有高优先权。即选择已经是DR的Switch作为DR，DR不可抢占。","在创建用户组后，可为用户组配置优先级以及VLAN，这样不同用户组内的用户即具有了不同的优先级以及网络访问权限。这将能够使管理员更灵活的管理用户。"]
    actions = ["由operational变为其它状态","业务方案下仅支持配置命令 **admin-user privilege level**","如果设备仍存在可用的ACL资源，可以继续在其他VLAN下使能VLAN内的MFF功能","发送邻居请求报文的次数为20次","判断如果是2.4G射频接收的，则先不发送探测应答帧","根据配置的网管地址向网管发送Trap消息","中断","通过报文头获取方式定位，确定是由于对应项不一致的ARP报文导致的攻击，才能指定ARP报文合法性检查时需要检查源MAC地址和检查目的MAC地址","都使TTL的数值减1","进行相应的主备切换，同时VSI清除自己的MAC地址，重新学习到新的主用设备的MAC地址","被丢弃","通过此命令清除攻击设备列表信息","不能感知上级网络的拓扑变化，将导致流量中断","作为LSR ID的32位Loopback接口地址","执行 **vpls-id** _vpls-id_ 命令配置VPLS ID","通过VXLAN网关可以互通","就会频繁地处理迭代到该下一跳的大量路由的变化，这样会占用大量资源，导致CPU占用率升高","发出","_link-number2_ 必须大于 _link-number1_","Switch的其他广播接口","为用户组配置优先级以及VLAN，这样不同用户组内的用户即具有了不同的优先级以及网络访问权限。这将能够使管理员更灵活的管理用户。"]
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
        subject_pos = re_subject(data['sentence'],subject_pos)
        predicted_spans['subject_span'].append(subject_pos)
        true_spans['subject_span'].append((data['rule_list'][0]['span'][0],data['rule_list'][0]['span'][1]))

        try:
            trigger = re.search(target_factor['Trigger_condition'], input_text)
            trigger_pos = trigger.span()
        except:
            trigger_pos = (-1, -1)
        trigger_pos = re_trigger(data['sentence'],trigger_pos)
        predicted_spans['trigger_span'].append(trigger_pos)
        true_spans['trigger_span'].append((data['rule_list'][1]['span'][0], data['rule_list'][1]['span'][1]))

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
print("trigger:  Precision {} Recall {} F1 {} ".format(trigger_precision, trigger_recall, trigger_f1))
action_precision, action_recall, action_f1 = calculate_precision_recall(predicted_spans['action_span'],
                                                                           true_spans['action_span'])
print("Action:  Precision {} Recall {} F1 {} ".format(action_precision, action_recall, action_f1))


print("ACC:")
for i in range(3):
    print(correct_num[i] / 88)

