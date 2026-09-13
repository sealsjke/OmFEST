import os
import vk_api
import json
from vk_api.longpoll import VkLongPoll, VkEventType

def main():
	TOKEN = os.getenv("VK_API_KEY")
	FLAG = os.getenv("FLAG")
	QUESTIONS = json.loads(open("questions.json").read())
	USERS = {}

	vk_session = vk_api.VkApi(token=TOKEN)
	longpoll = VkLongPoll(vk_session)
	
	print("Бот запущен и слушает сообщения...")
	for event in longpoll.listen():
		if event.type == VkEventType.MESSAGE_NEW and event.to_me:
			msg_text = event.text.lower()
			user_id = event.user_id
			user_key = str(user_id)

			if msg_text == "Начать".lower():
				USERS[user_key] = 0
				vk_session.method('messages.send', {
					'user_id': user_id,
					'message': f"Добро пожаловать на экзамен по истории Омского CTF движения!\n\nВопрос {USERS[user_key] + 1}/{len(QUESTIONS)}\n\n{QUESTIONS[USERS[user_key]]['question']}",
					'random_id': 0
				})
			elif any(msg_text == i.lower() for i in QUESTIONS[USERS[user_key]]["answer"]):
				USERS[user_key] += 1
				question = f"Вопрос {USERS[user_key] + 1}/{len(QUESTIONS)}\n\n{QUESTIONS[USERS[user_key]]['question']}"
				if USERS[user_key] == len(QUESTIONS):
					vk_session.method('messages.send', {
						'user_id': user_id,
						'message': FLAG,
						'random_id': 0
					})
					USERS[user_key] = 0
				else:
					vk_session.method('messages.send', {
						'user_id': user_id,
						'message': question,
						'random_id': 0
					})
			else:
				USERS[user_key] = 0
				question = f"Вопрос {USERS[user_key] + 1}/{len(QUESTIONS)}\n\n{QUESTIONS[USERS[user_key]]['question']}"
				vk_session.method('messages.send', {
					'user_id': user_id,
					'message': "Неверный ответ!",
					'random_id': 0
				})

				vk_session.method('messages.send', {
					'user_id': user_id,
					'message': question,
					'random_id': 0
				})

if __name__ == "__main__":
	main()
