"""Optional official-model decision core. Requires the actual official client."""
import json


def decide(*, task, observation, history, action_history, state):
    from third_party_agent import model

    messages = [
        {'role': 'system', 'content':
         '你是网页任务智能体。根据任务、当前页面与历史决定下一步。每次只返回一个 JSON action。'
         '元素编号必须来自当前观察。不要假设上一步已成功；从页面确认目标达成后才 stop。'
         '可用动作的完整格式以运行环境提供的协议为准。'},
        {'role': 'user', 'content': json.dumps({
            'task': task, 'observation': observation,
            'recent_actions': action_history[-8:], 'memory': state.get('memory', '')
        }, ensure_ascii=False)},
    ]
    reply = model.generate(messages)
    text = reply.text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1].rsplit('```', 1)[0]
    action = json.loads(text)['action']
    if not isinstance(action, str):
        raise ValueError('Expected string action')
    return {'action': action, 'model_calls': 1}
