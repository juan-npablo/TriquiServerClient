import socket
import threading
import json
import random
import tkinter as tk
from tkinter import messagebox

class TicTacToeServer:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('localhost', 5555))
        self.server.listen(5)
        
        self.clients = []
        self.spectators = []
        self.players = []
        self.names = {}
        self.client_by_name = {}
        self.current_player = None
        self.board = ['' for _ in range(9)]
        self.game_state = {
            'board': self.board,
            'current_player': None,
            'scores': {'player1': 0, 'player2': 0},
            'round': 1,
            'symbols': {}
        }
        
        # GUI
        self.window = tk.Tk()
        self.window.title("Tic Tac Toe Server")
        self.status_label = tk.Label(self.window, text="Esperando jugadores...")
        self.status_label.pack()
        
        print("Servidor iniciado...")
        
        # Iniciar thread para aceptar conexiones
        self.accept_thread = threading.Thread(target=self.accept_connections)
        self.accept_thread.daemon = True
        self.accept_thread.start()
        
        self.window.mainloop()
    
    def accept_connections(self):
        while len(self.players) < 2 or len(self.spectators) < 3:
            try:
                client, addr = self.server.accept()
                print(f"Cliente conectado desde {addr}")
                self.clients.append(client)
                
                # Recibir nombre del cliente
                name = client.recv(1024).decode()
                print(f"Nombre recibido: {name}")
                self.names[client] = name
                self.client_by_name[name] = client
                
                if len(self.players) < 2:
                    self.players.append(client)
                    if len(self.players) == 2:
                        self.start_game()
                    client.send("PLAYER".encode())
                else:
                    self.spectators.append(client)
                    client.send("SPECTATOR".encode())
                
                threading.Thread(target=self.handle_client, args=(client,)).start()
                self.update_status()
            except Exception as e:
                print(f"Error al aceptar conexiones: {e}")
                break
    
    def start_game(self):
        symbols = ['X', 'O']
        random.shuffle(symbols)
        player1_name = self.names[self.players[0]]
        player2_name = self.names[self.players[1]]
        self.game_state['symbols'][player1_name] = symbols[0]
        self.game_state['symbols'][player2_name] = symbols[1]
        
        self.current_player = random.choice(self.players)
        self.game_state['current_player'] = self.names[self.current_player]
        
        self.broadcast_game_state()
    
    def handle_client(self, client):
        while True:
            try:
                message = client.recv(1024).decode()
                if not message:
                    break
                
                data = json.loads(message)
                if data['type'] == 'move':
                    if client == self.current_player:
                        position = data['position']
                        if self.is_valid_move(position):
                            self.make_move(client, position)
            except Exception as e:
                print(f"Error al manejar cliente: {e}")
                break
        
        self.remove_client(client)
    
    def is_valid_move(self, position):
        return self.board[position] == ''
    
    def make_move(self, client, position):
        player_name = self.names[client]
        self.board[position] = self.game_state['symbols'][player_name]
        self.game_state['board'] = self.board
        
        if self.check_winner():
            self.handle_win(client)
        elif '' not in self.board:
            self.handle_draw()
        else:
            self.switch_player()
            self.broadcast_game_state()
    
    def check_winner(self):
        wins = [(0,1,2), (3,4,5), (6,7,8),
                (0,3,6), (1,4,7), (2,5,8),
                (0,4,8), (2,4,6)]
        
        for win in wins:
            if (self.board[win[0]] == self.board[win[1]] == self.board[win[2]] != ''):
                return True
        return False
    
    def handle_win(self, winner):
        player_index = self.players.index(winner)
        player_key = f'player{player_index + 1}'
        self.game_state['scores'][player_key] += 1
        
        if self.game_state['scores'][player_key] == 2:
            self.end_game(winner)
        else:
            self.start_new_round()
    
    def handle_draw(self):
        self.start_new_round()
    
    def start_new_round(self):
        self.board = ['' for _ in range(9)]
        self.game_state['board'] = self.board
        self.game_state['round'] += 1
        
        self.current_player = self.players[1] if self.current_player == self.players[0] else self.players[0]
        self.game_state['current_player'] = self.names[self.current_player]
        
        self.broadcast_game_state()
    
    def end_game(self, winner):
        self.game_state['winner'] = self.names[winner]
        self.broadcast_game_state()
        
        self.board = ['' for _ in range(9)]
        self.game_state['board'] = self.board
        self.game_state['scores'] = {'player1': 0, 'player2': 0}
        self.game_state['round'] = 1
        self.game_state['symbols'] = {}
    
    def switch_player(self):
        self.current_player = self.players[1] if self.current_player == self.players[0] else self.players[0]
        self.game_state['current_player'] = self.names[self.current_player]
    
    def broadcast_game_state(self):
        message = json.dumps(self.game_state)
        for client in self.clients:
            try:
                if message:
                    client.send(message.encode())
                else:
                    print("Mensaje vacío no enviado")
            except Exception as e:
                print(f"Error al enviar estado del juego: {e}")
                self.remove_client(client)
    
    def remove_client(self, client):
        if client in self.clients:
            self.clients.remove(client)
        if client in self.players:
            self.players.remove(client)
        if client in self.spectators:
            self.spectators.remove(client)
        if client in self.names:
            name = self.names[client]
            del self.client_by_name[name]
            del self.names[client]
        self.update_status()
    
    def update_status(self):
        status = f"Jugadores conectados: {len(self.players)}/2\n"
        status += f"Espectadores: {len(self.spectators)}/3"
        self.status_label.config(text=status)

if __name__ == "__main__":
    server = TicTacToeServer()
