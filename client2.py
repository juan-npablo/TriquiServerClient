import socket
import json
import tkinter as tk
from tkinter import messagebox
import threading

class TicTacToeClient:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(('localhost', 5555))
        
        # GUI inicial para el nombre
        self.setup_name_window()
    
    def setup_name_window(self):
        self.name_window = tk.Tk()
        self.name_window.title("Ingresar Nombre")
        
        tk.Label(self.name_window, text="Ingrese su nombre:").pack()
        self.name_entry = tk.Entry(self.name_window)
        self.name_entry.pack()
        
        tk.Button(self.name_window, text="Conectar", command=self.submit_name).pack()
        
        self.name_window.mainloop()
    
    def submit_name(self):
        self.name = self.name_entry.get()
        if self.name:
            self.client.send(self.name.encode())
            self.role = self.client.recv(1024).decode()
            self.name_window.destroy()
            self.setup_game_window()
    
    def setup_game_window(self):
        self.window = tk.Tk()
        self.window.title(f"Tic Tac Toe - {self.name} ({self.role})")
        
        # Frame superior para información
        info_frame = tk.Frame(self.window)
        info_frame.pack()
        
        self.status_label = tk.Label(info_frame, text="Esperando inicio del juego...")
        self.status_label.pack()
        
        self.score_label = tk.Label(info_frame, text="Puntaje: 0 - 0")
        self.score_label.pack()
        
        # Frame para el tablero
        board_frame = tk.Frame(self.window)
        board_frame.pack()
        
        self.buttons = []
        for i in range(3):
            row = []
            for j in range(3):
                button = tk.Button(board_frame, text="", width=10, height=4,
                                 command=lambda x=i, y=j: self.make_move(x*3 + y))
                button.grid(row=i, column=j)
                row.append(button)
            self.buttons.append(row)
        
        # Iniciar thread para recibir actualizaciones
        threading.Thread(target=self.receive_updates).start()
        
        self.window.mainloop()
    
    def make_move(self, position):
        message = {
            'type': 'move',
            'position': position
        }
        try:
            self.client.send(json.dumps(message).encode())
        except:
            messagebox.showerror("Error", "No se pudo enviar el movimiento")
    
    def receive_updates(self):
        while True:
            try:
                message = self.client.recv(1024).decode()
                if not message:
                    break
                
                game_state = json.loads(message)
                self.update_board(game_state)
                self.update_status(game_state)
                
                if 'winner' in game_state:
                    messagebox.showinfo("Fin del juego", 
                                      f"¡{game_state['winner']} ha ganado el juego!")
            except:
                messagebox.showerror("Error", "Se perdió la conexión con el servidor")
                break
        
        self.window.destroy()
    
    def update_board(self, game_state):
        board = game_state['board']
        current_player = game_state['current_player']
        
        for i in range(9):
            row = i // 3
            col = i % 3
            self.buttons[row][col]['text'] = board[i]
            
            # Habilitar/deshabilitar botones según el turno
            if self.role == "PLAYER":
                if board[i] == '':  # Casilla vacía
                    if current_player == self.name:  # Es mi turno
                        self.buttons[row][col]['state'] = 'normal'
                    else:  # No es mi turno
                        self.buttons[row][col]['state'] = 'disabled'
                else:  # Casilla ocupada
                    self.buttons[row][col]['state'] = 'disabled'
            else:  # Es espectador
                self.buttons[row][col]['state'] = 'disabled'
    
    def update_status(self, game_state):
        if 'current_player' in game_state:
            status = f"Turno de: {game_state['current_player']}"
            self.status_label.config(text=status)
        
        score_text = f"Ronda {game_state['round']}: "
        score_text += f"Jugador 1: {game_state['scores']['player1']} - "
        score_text += f"Jugador 2: {game_state['scores']['player2']}"
        self.score_label.config(text=score_text)

if __name__ == "__main__":
    client = TicTacToeClient()