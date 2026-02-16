from core.chat_service import (
    create_new_chat,
    get_all_chats,
    switch_chat,
    delete_chat,
    get_active_chat
)

from core.llm import generate
from core.prompt import build_prompt
from core.memory import get_relevant_memories, add_memory
from database.messages import add_message, get_recent_messages
from config.settings import PERSONA_NAME


def show_menu():
    print("\n--- Chat Manager ---")
    print("1. New Chat")
    print("2. List Chats")
    print("3. Switch Chat")
    print("4. Delete Chat")
    print("5. Continue Chat")
    print("6. Exit")


def main():
    with open("personas/christina.txt", "r") as f:
        character = f.read()

    print(f"{PERSONA_NAME} CLI started.")

    while True:
        show_menu()
        choice = input("Select option: ")

        if choice == "1":
            title = input("Enter chat title: ")
            chat_id = create_new_chat(title)
            print(f"Created chat {chat_id}")

        elif choice == "2":
            chats = get_all_chats()
            for c in chats:
                print(f"{c[0]} - {c[1]}")

        elif choice == "3":
            chat_id = int(input("Enter chat ID: "))
            switch_chat(chat_id)
            print("Switched.")

        elif choice == "4":
            chat_id = int(input("Enter chat ID: "))
            delete_chat(chat_id)
            print("Deleted.")

        elif choice == "5":
            chat_id = get_active_chat()
            if not chat_id:
                print("No active chat. Create or switch first.")
                continue

            user_input = input("You: ")

            memories = get_relevant_memories(chat_id, user_input)
            conversation = get_recent_messages(chat_id)

            prompt = build_prompt(character, memories, conversation, user_input)
            reply = generate(prompt)

            add_message(chat_id, "User", user_input)
            add_message(chat_id, PERSONA_NAME, reply)

            print(f"{PERSONA_NAME}: {reply}")

        elif choice == "6":
            break

