# src/utils/log_manager.py
import logging
import os
import shutil
import zipfile
from datetime import datetime, timedelta
from typing import Dict
from flask import request

class LogManager:
    """Gerencia o logging com rastreamento de IP e ações dos usuários."""

    def __init__(self):
        self.logger = logging.getLogger("DashboardLogger")
        self.logger.setLevel(logging.INFO)

        # File handler
        fh = logging.FileHandler("dashboard_activity.log")
        fh.setLevel(logging.INFO)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - IP: %(ip)s - %(message)s"
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        self.active_users = {}
        self.connected_ips = set()
        self._last_log = {}  # Para controlar frequência de logs

    def log_with_ip(self, level, message):
        """Log message with IP address from Flask request context."""
        try:
            # Tenta obter o IP do request do Flask
            from flask import request
            try:
                ip = request.remote_addr
            except RuntimeError:
                ip = "system"
        except Exception:
            ip = "system"

        # Controle de frequência de logs
        current_time = datetime.now()
        log_key = f"{ip}_{message}"
        
        if log_key in self._last_log:
            # Só loga novamente após 5 minutos para a mesma mensagem do mesmo IP
            if (current_time - self._last_log[log_key]).total_seconds() < 300:
                return
            
        self._last_log[log_key] = current_time

        try:
            if ip != "system" and ip not in self.connected_ips:
                self.connected_ips.add(ip)
                self.logger.info(f"Nova conexão de IP: {ip}", extra={"ip": ip})

            if level.upper() == "INFO":
                self.logger.info(message, extra={"ip": ip})
            elif level.upper() == "WARNING":
                self.logger.warning(message, extra={"ip": ip})
            elif level.upper() == "ERROR":
                self.logger.error(message, extra={"ip": ip})
        except Exception as e:
            self.logger.error(f"Erro ao registrar log: {str(e)}", extra={"ip": "error"})

    def add_active_user(self, ip):
        """Adiciona um usuário ativo."""
        if ip not in self.active_users:
            self.active_users[ip] = {
                "connected_at": datetime.now(),
                "last_activity": datetime.now(),
                "action_count": 0,
            }
            self.log_with_ip("INFO", f"Novo usuário conectado de {ip}")

    def update_user_activity(self, ip, action):
        """Atualiza atividade do usuário."""
        if ip in self.active_users:
            self.active_users[ip]["last_activity"] = datetime.now()
            self.active_users[ip]["action_count"] += 1
            self.log_with_ip("INFO", f"Usuário {ip}: {action}")

    def get_active_users_report(self):
        """Retorna relatório de usuários ativos."""
        now = datetime.now()
        return {
            ip: {
                "connected_for": str(now - info["connected_at"]),
                "last_activity": str(now - info["last_activity"]),
                "actions": info["action_count"],
            }
            for ip, info in self.active_users.items()
        }

    def get_connected_ips(self):
        """Return set of currently connected IPs."""
        return self.connected_ips

    def clear_old_logs(self, days: int = 30):
        """Limpa logs antigos do arquivo de log."""
        try:
            log_file = "dashboard_activity.log"
            if not os.path.exists(log_file):
                return
            
            # Lê todas as linhas do arquivo
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Filtra apenas logs recentes
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_logs = []
            
            for line in lines:
                try:
                    # Extrai a data do log (assume formato padrão no início da linha)
                    log_date_str = line.split('-')[0].strip()
                    log_date = datetime.strptime(log_date_str, "%Y-%m-%d %H:%M:%S,%f")
                    
                    if log_date >= cutoff_date:
                        recent_logs.append(line)
                except (ValueError, IndexError):
                    # Se não conseguir extrair a data, mantém o log
                    recent_logs.append(line)
            
            # Reescreve o arquivo apenas com logs recentes
            with open(log_file, 'w', encoding='utf-8') as f:
                f.writelines(recent_logs)
                
            self.logger.info(f"Logs mais antigos que {days} dias foram removidos")
            
        except Exception as e:
            self.logger.error(f"Erro ao limpar logs antigos: {str(e)}")

    def backup_logs(self, backup_dir: str = "log_backups"):
        """Cria backup dos logs atuais."""
        try:
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"dashboard_activity_{timestamp}.log")
            
            # Copia o arquivo de log atual
            if os.path.exists("dashboard_activity.log"):
                shutil.copy2("dashboard_activity.log", backup_file)
                
                # Compacta o backup
                with zipfile.ZipFile(f"{backup_file}.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(backup_file, os.path.basename(backup_file))
                
                # Remove o arquivo não compactado
                os.remove(backup_file)
                
                self.logger.info(f"Backup dos logs criado: {backup_file}.zip")
            else:
                self.logger.warning("Arquivo de log não encontrado para backup")
            
        except Exception as e:
            self.logger.error(f"Erro ao criar backup dos logs: {str(e)}")

    def get_log_statistics(self) -> Dict:
        """Retorna estatísticas dos logs."""
        stats = {
            "total_users": len(self.active_users),
            "total_connections": len(self.connected_ips),
            "active_users": len([u for u, info in self.active_users.items() 
                               if (datetime.now() - info["last_activity"]).seconds < 3600]),
            "total_actions": sum(info["action_count"] for info in self.active_users.values()),
            "last_connection": None,
            "most_active_ip": None,
            "most_actions": 0
        }
        
        if self.active_users:
            # Encontra o usuário mais recente
            latest_user = max(self.active_users.items(), 
                            key=lambda x: x[1]["last_activity"])
            stats["last_connection"] = latest_user[1]["last_activity"]
            
            # Encontra o usuário mais ativo
            most_active = max(self.active_users.items(), 
                            key=lambda x: x[1]["action_count"])
            stats["most_active_ip"] = most_active[0]
            stats["most_actions"] = most_active[1]["action_count"]
        
        return stats

    def cleanup_inactive_users(self, timeout_minutes: int = 30):
        """Remove usuários inativos."""
        now = datetime.now()
        timeout = timedelta(minutes=timeout_minutes)
        
        inactive_users = [
            ip for ip, info in self.active_users.items()
            if now - info["last_activity"] > timeout
        ]
        
        for ip in inactive_users:
            self.log_with_ip("INFO", f"Removendo usuário inativo: {ip}")
            del self.active_users[ip]
            if ip in self.connected_ips:
                self.connected_ips.remove(ip)
