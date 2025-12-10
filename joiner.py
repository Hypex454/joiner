from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import requests
import re
from datetime import datetime
import socket
import netifaces
import threading
import time
import subprocess
import atexit
import os

app = FastAPI(title="Discord Brainrot Notifications API")

# Configurar CORS para permitir acesso de qualquer lugar
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurações
DISCORD_BOT_TOKEN = "MTQyNTA2NjI5ODY0NzI0ODkwNw.Gkf9KZ.ebSGU7UQR-rNtfStGc939AeT5kTIC6SRaj8Op0"
DISCORD_CHANNELS = [
    "1430330769456365578",
    "1430330769456365578", 
    "1430330769456365578",
    "1430330769456365578"
]

# CAMINHO DIRETO DO NGROK - USE SEU CAMINHO
NGROK_PATH = r"C:\Users\Pedro\Desktop\Projetos\ngrok.exe"

# Variáveis globais para ngrok
ngrok_process = None
ngrok_url = None

class BrainrotNotification(BaseModel):
    message_id: str
    brainrot_name: str
    generation_rate: str
    job_id: str
    channel_id: str
    timestamp: str
    players: Optional[str] = None
    base_name: Optional[str] = None

processed_messages = {}

for channel_id in DISCORD_CHANNELS:
    processed_messages[channel_id] = set()

def start_ngrok_tunnel(port=8000):
    """Inicia um túnel ngrok para acesso externo usando caminho direto"""
    global ngrok_process, ngrok_url
    
    try:
        print("🚀 Iniciando túnel ngrok...")
        
        # Verificar se o ngrok existe no caminho especificado
        if not os.path.exists(NGROK_PATH):
            print(f"❌ Ngrok não encontrado em: {NGROK_PATH}")
            print("📥 Para acesso externo, baixe ngrok de: https://ngrok.com/download")
            print("💡 E extraia ngrok.exe na pasta: C:\\Users\\Pedro\\Desktop\\Projetos\\")
            return None
        
        print(f"✅ Ngrok encontrado em: {NGROK_PATH}")
        
        # Iniciar ngrok com caminho direto
        ngrok_process = subprocess.Popen(
            [NGROK_PATH, 'http', str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True
        )
        
        # Aguardar ngrok iniciar
        print("⏳ Aguardando ngrok iniciar (pode levar até 10 segundos)...")
        time.sleep(8)  # Dar mais tempo para o ngrok inicializar
        
        # Tentar obter URL do ngrok com múltiplas tentativas
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                print(f"🔍 Tentando obter URL do ngrok ({attempt + 1}/{max_attempts})...")
                response = requests.get('http://localhost:4040/api/tunnels', timeout=10)
                if response.status_code == 200:
                    tunnels = response.json()
                    if tunnels['tunnels']:
                        public_url = tunnels['tunnels'][0]['public_url']
                        ngrok_url = public_url
                        print(f"✅ Ngrok tunnel criado: {public_url}")
                        return public_url
                time.sleep(2)
            except requests.exceptions.RequestException as e:
                print(f"⏳ Ngrok ainda iniciando... ({attempt + 1}/{max_attempts})")
                time.sleep(3)
        
        print("❌ Não foi possível obter URL do ngrok automaticamente.")
        print("💡 Soluções:")
        print("1. Abra manualmente: http://localhost:4040")
        print("2. Ou execute em outro terminal: ngrok http 8000")
        return None
            
    except Exception as e:
        print(f"❌ Erro ao iniciar ngrok: {e}")
        print("\n🔧 SOLUÇÃO ALTERNATIVA:")
        print("1. Abra um terminal/prompt de comando")
        print("2. Navegue até: C:\\Users\\Pedro\\Desktop\\Projetos\\")
        print("3. Execute: ngrok.exe http 8000")
        print("4. Copie a URL que aparecer (ex: https://abcd-1234.ngrok.io)")
        print("5. Use esta URL no script Lua")
        return None

def stop_ngrok_tunnel():
    """Para o túnel ngrok"""
    global ngrok_process
    if ngrok_process:
        print("🛑 Parando túnel ngrok...")
        ngrok_process.terminate()
        ngrok_process = None

def get_network_info():
    """Obtém informações de rede para mostrar como conectar"""
    print("🌐 Obtendo informações de rede...")
    
    try:
        # Obter IP local
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Tentar obter IP público
        try:
            public_ip = requests.get('https://api.ipify.org', timeout=5).text
        except:
            public_ip = "Não disponível"
        
        # Obter todos os IPs da rede
        network_ips = []
        for interface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr['addr']
                    if not ip.startswith('127.'):
                        network_ips.append(ip)
        
        return {
            "hostname": hostname,
            "local_ip": local_ip,
            "public_ip": public_ip,
            "network_ips": network_ips,
            "ngrok_url": ngrok_url,
            "ngrok_available": os.path.exists(NGROK_PATH)
        }
    except Exception as e:
        print(f"❌ Erro ao obter informações de rede: {e}")
        return {
            "hostname": "N/A",
            "local_ip": "N/A", 
            "public_ip": "N/A",
            "network_ips": [],
            "ngrok_url": ngrok_url,
            "ngrok_available": os.path.exists(NGROK_PATH)
        }

def test_bot_permissions():
    """Testa se o bot tem permissões para acessar os canais"""
    print("🔐 Testando permissões do bot...")
    
    for channel_id in DISCORD_CHANNELS:
        headers = {
            "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
            "Content-Type": "application/json"
        }
        
        url = f"https://discord.com/api/v10/channels/{channel_id}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                channel_data = response.json()
                print(f"✅ Canal {channel_id}: Acesso permitido - {channel_data.get('name', 'N/A')}")
            elif response.status_code == 403:
                print(f"❌ Canal {channel_id}: Acesso negado - Bot sem permissões")
            elif response.status_code == 404:
                print(f"❌ Canal {channel_id}: Não encontrado - ID inválido ou bot não está no servidor")
            else:
                print(f"⚠️ Canal {channel_id}: Status {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Erro ao testar canal {channel_id}: {e}")

def fetch_discord_messages(channel_id: str, last_message_id: Optional[str] = None):
    """Busca mensagens de um canal específico do Discord"""
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=10"
    
    try:
        print(f"📡 Buscando mensagens do canal {channel_id}...")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 403:
            print(f"❌ Acesso negado ao canal {channel_id} - Verifique as permissões do bot")
            return None
        elif response.status_code == 404:
            print(f"❌ Canal {channel_id} não encontrado")
            return None
        elif response.status_code == 401:
            print(f"❌ Token inválido para o canal {channel_id}")
            return None
        
        response.raise_for_status()
        messages = response.json()
        
        print(f"✅ Canal {channel_id}: {len(messages)} mensagens encontradas")
        
        # Filtrar mensagens novas se last_message_id for fornecido
        if last_message_id:
            new_messages = []
            for msg in messages:
                if msg['id'] == last_message_id:
                    break
                new_messages.append(msg)
            print(f"📨 Canal {channel_id}: {len(new_messages)} novas mensagens desde {last_message_id}")
            return new_messages
        else:
            print(f"📨 Canal {channel_id}: {len(messages)} mensagens (busca inicial)")
            return messages
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao buscar mensagens do canal {channel_id}: {e}")
        return None
    except Exception as e:
        print(f"❌ Erro inesperado no canal {channel_id}: {e}")
        return None

def parse_brainrot_embed(message_data: dict, channel_id: str) -> Optional[BrainrotNotification]:
    try:
        if not message_data.get('embeds'):
            print(f"📭 Mensagem {message_data['id']} sem embeds - ignorando")
            return None
        
        embed = message_data['embeds'][0]
        print(f"🔍 Processando embed do canal {channel_id}")
        
        # Juntar TODOS os dados do embed para análise
        full_text = ""
        
        # Adicionar título se existir
        title = embed.get('title', '')
        if title:
            full_text += f"TÍTULO: {title}\n"
            print(f"📌 Título: {title}")
        
        # Adicionar descrição se existir
        description = embed.get('description', '')
        if description:
            full_text += f"DESCRIÇÃO: {description}\n"
        
        # Adicionar fields se existirem
        if embed.get('fields'):
            for field in embed['fields']:
                field_name = field.get('name', '')
                field_value = field.get('value', '')
                full_text += f"FIELD_{field_name}: {field_value}\n"
                print(f"📋 Field: {field_name} = {field_value}")
        
        # Adicionar footer se existir
        footer = embed.get('footer', {})
        if footer.get('text'):
            full_text += f"FOOTER: {footer['text']}\n"
        
        # Adicionar author se existir
        author = embed.get('author', {})
        if author.get('name'):
            full_text += f"AUTHOR: {author['name']}\n"
        
        print(f"📄 CONTEÚDO COMPLETO DO EMBED:\n{full_text}")
        print("🎯 PROCURANDO PADRÕES...")
        
        # EXTRAIR INFORMAÇÕES COM MÚLTIPLOS PADRÕES
        
        brainrot_name = "Brainrot Desconhecido"
        generation_rate = "0"
        job_id = None
        players = None
        base_name = None
        
        # PADRÃO 1: Formato "Best: Candy - Los Tipi Tacos - ($2M/s)"
        best_patterns = [
            r'Best:\s*([^-]+)-([^-]+)-\s*\(\$([\d\.]+[MK]?)/s\)',
            r'Best:\s*([^-]+)\s*-\s*([^-]+)\s*-\s*\(\$([\d\.]+[MK]?)/s\)',
            r'BEST:\s*([^-]+)-([^-]+)-\s*\(\$([\d\.]+[MK]?)/s\)',
        ]
        
        for pattern in best_patterns:
            best_match = re.search(pattern, full_text, re.IGNORECASE)
            if best_match:
                candy_type = best_match.group(1).strip()
                brainrot_name = best_match.group(2).strip()
                generation_rate = best_match.group(3).strip()
                print(f"💰 PADRÃO BEST ENCONTRADO: {candy_type} - {brainrot_name} - ${generation_rate}/s")
                break
        
        # PADRÃO 2: Formato "• Candy - Los Tipi Tacos - ($2M/s)"
        bullet_patterns = [
            r'[•\-]\s*([^-]+)-([^-]+)-\s*\(\$([\d\.]+[MK]?)/s\)',
            r'[•\-]\s*([^-]+)\s*-\s*([^-]+)\s*-\s*\(\$([\d\.]+[MK]?)/s\)',
        ]
        
        if brainrot_name == "Brainrot Desconhecido":
            for pattern in bullet_patterns:
                bullet_match = re.search(pattern, full_text, re.IGNORECASE)
                if bullet_match:
                    candy_type = bullet_match.group(1).strip()
                    brainrot_name = bullet_match.group(2).strip()
                    generation_rate = bullet_match.group(3).strip()
                    print(f"💰 PADRÃO BULLET ENCONTRADO: {candy_type} - {brainrot_name} - ${generation_rate}/s")
                    break
        
        # PADRÃO 3: Qualquer padrão com taxa
        rate_patterns = [
            r'\(\$([\d\.]+[MK]?)/s\)',
            r'\$([\d\.]+[MK]?)/s',
            r'([\d\.]+[MK]?)/s',
        ]
        
        if brainrot_name == "Brainrot Desconhecido":
            for pattern in rate_patterns:
                rate_match = re.search(pattern, full_text, re.IGNORECASE)
                if rate_match:
                    generation_rate = rate_match.group(1).strip()
                    print(f"💰 TAXA ENCONTRADA: ${generation_rate}/s")
                    # Tentar extrair nome de outro campo
                    if title and title != "Finder":
                        brainrot_name = title
                    break
        
        # EXTRAIR JOB ID (UUID)
        job_patterns = [
            r'Job ID\s*([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})',
            r'Job ID:\s*([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})',
            r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})',
        ]
        
        # Procurar Job ID em fields específicos primeiro
        if embed.get('fields'):
            for field in embed['fields']:
                field_name = field.get('name', '').lower()
                field_value = field.get('value', '')
                
                if 'job' in field_name or 'id' in field_name:
                    print(f"🔎 Procurando Job ID no field: '{field_name}' = '{field_value}'")
                    for pattern in job_patterns:
                        job_match = re.search(pattern, field_value, re.IGNORECASE)
                        if job_match:
                            job_id = job_match.group(1).lower()
                            print(f"🎯 Job ID encontrado no field '{field_name}': {job_id}")
                            break
                    if job_id:
                        break
        
        # Se não encontrou nos fields, procurar em todo o texto
        if not job_id:
            for pattern in job_patterns:
                job_match = re.search(pattern, full_text, re.IGNORECASE)
                if job_match:
                    job_id = job_match.group(1).lower()
                    print(f"🎯 Job ID encontrado no texto: {job_id}")
                    break
        
        # EXTRAIR PLAYERS
        players_patterns = [
            r'Players:\s*(\d+/\d+)',
            r'Players\s*(\d+/\d+)',
            r'Jogadores:\s*(\d+/\d+)',
        ]
        
        for pattern in players_patterns:
            players_match = re.search(pattern, full_text, re.IGNORECASE)
            if players_match:
                players = players_match.group(1)
                print(f"👥 Players encontrados: {players}")
                break
        
        # EXTRAIR BASE NAME
        base_patterns = [
            r'Base:\s*(.+)',
            r'Base\s*(.+)',
        ]
        
        for pattern in base_patterns:
            base_match = re.search(pattern, full_text)
            if base_match:
                base_name = base_match.group(1).strip()
                print(f"🏠 Base encontrada: {base_name}")
                break
        
        # SE NÃO ENCONTROU NADA, TENTAR USAR O TÍTULO COMO NOME
        if brainrot_name == "Brainrot Desconhecido" and title and title != "Finder":
            brainrot_name = title
            print(f"🏷️ Usando título como nome: {brainrot_name}")
        
        # VALIDAÇÃO FINAL
        if job_id and brainrot_name != "Brainrot Desconhecido":
            print(f"✅ NOTIFICAÇÃO VÁLIDA ENCONTRADA:")
            print(f"   🏷️  Nome: {brainrot_name}")
            print(f"   💰 Taxa: ${generation_rate}/s")
            print(f"   🎯 Job ID: {job_id}")
            print(f"   👥 Players: {players}")
            print(f"   🏠 Base: {base_name}")
            
            return BrainrotNotification(
                message_id=message_data['id'],
                brainrot_name=brainrot_name,
                generation_rate=generation_rate,
                job_id=job_id,
                channel_id=channel_id,
                timestamp=datetime.utcnow().isoformat(),
                players=players,
                base_name=base_name
            )
        else:
            print(f"❌ NÃO É UMA NOTIFICAÇÃO BRAINROT VÁLIDA")
            if not job_id:
                print("   ❌ Job ID não encontrado")
            if brainrot_name == "Brainrot Desconhecido":
                print("   ❌ Nome do brainrot não identificado")
            
            # DEBUG: Mostrar o que foi encontrado
            print(f"   🔍 Resumo encontrado:")
            print(f"      Nome: {brainrot_name}")
            print(f"      Taxa: {generation_rate}")
            print(f"      Job ID: {job_id}")
            
            return None
    
    except Exception as e:
        print(f"❌ ERRO ao processar embed do canal {channel_id}: {e}")
        import traceback
        print(f"🔍 Stack trace: {traceback.format_exc()}")
    
    return None

# Endpoints da API (mantenha os mesmos endpoints)
@app.get("/api/debug/messages")
async def debug_messages(channel_id: str):
    """Endpoint para debug de mensagens de um canal específico"""
    try:
        print(f"🔍 DEBUG: Buscando mensagens do canal {channel_id}")
        
        messages = fetch_discord_messages(channel_id)
        
        if not messages:
            return {"success": False, "message": f"Nenhuma mensagem no canal {channel_id}"}
        
        debug_info = []
        
        for i, message in enumerate(messages[:5]):
            message_debug = {
                "index": i,
                "message_id": message['id'],
                "has_embeds": bool(message.get('embeds')),
                "content": message.get('content', '')[:100] + "..." if len(message.get('content', '')) > 100 else message.get('content', '')
            }
            
            if message.get('embeds'):
                embed = message['embeds'][0]
                message_debug["embed_title"] = embed.get('title', 'Sem título')
                message_debug["embed_description"] = embed.get('description', 'Sem descrição')[:100] + "..." if len(embed.get('description', '')) > 100 else embed.get('description', '')
                
                notification = parse_brainrot_embed(message, channel_id)
                message_debug["is_brainrot"] = bool(notification)
                if notification:
                    message_debug["brainrot_name"] = notification.brainrot_name
                    message_debug["generation_rate"] = notification.generation_rate
                    message_debug["job_id"] = notification.job_id
            
            debug_info.append(message_debug)
        
        return {
            "success": True,
            "channel_id": channel_id,
            "total_messages": len(messages),
            "debug_messages": debug_info
        }
        
    except Exception as e:
        print(f"❌ Erro no debug: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/messages/new")
async def get_new_messages(last_message_ids: Optional[str] = None):
    """Endpoint para buscar novas mensagens de TODOS os 4 canais - COMPATÍVEL COM LUA"""
    try:
        print(f"🔍 Buscando mensagens em {len(DISCORD_CHANNELS)} canais...")
        
        last_ids = {}
        if last_message_ids:
            print(f"📝 Last IDs recebidos: {last_message_ids}")
            for pair in last_message_ids.split(','):
                if ':' in pair:
                    channel_id, msg_id = pair.split(':', 1)
                    last_ids[channel_id] = msg_id
                    print(f"   📋 Canal {channel_id}: último ID = {msg_id}")
        
        all_notifications = []
        channels_processed = 0
        
        for channel_id in DISCORD_CHANNELS:
            print(f"\n📡 Verificando canal: {channel_id}")
            
            channel_last_id = last_ids.get(channel_id)
            if channel_last_id:
                print(f"   📌 Buscando mensagens desde ID: {channel_last_id}")
            else:
                print(f"   📌 Buscando últimas 10 mensagens (busca inicial)")
            
            messages = fetch_discord_messages(channel_id, channel_last_id)
            
            if messages is None:
                print(f"   ❌ Falha ao buscar mensagens do canal {channel_id}")
                continue
            
            if not messages:
                print(f"   ℹ️ Nenhuma nova mensagem no canal {channel_id}")
                continue
            
            channel_notifications = []
            
            for message in messages:
                if message['id'] in processed_messages[channel_id]:
                    print(f"   ⏭️ Mensagem {message['id']} já processada - pulando")
                    continue
                    
                print(f"   📩 Processando mensagem ID: {message['id']}")
                
                notification = parse_brainrot_embed(message, channel_id)
                if notification:
                    print(f"   ✅ Notificação extraída: {notification.brainrot_name}")
                    channel_notifications.append(notification)
                    processed_messages[channel_id].add(message['id'])
                else:
                    print(f"   ❌ Mensagem {message['id']} não contém notificação válida")
            
            all_notifications.extend(channel_notifications)
            channels_processed += 1
            
            print(f"   📊 Canal {channel_id}: {len(channel_notifications)} notificações encontradas")
        
        all_notifications.sort(key=lambda x: x.message_id, reverse=True)
        
        response_message = f"Processados {channels_processed}/{len(DISCORD_CHANNELS)} canais - {len(all_notifications)} novas notificações"
        print(f"✅ {response_message}")
        
        return {
            "success": True,
            "new_messages": [
                {
                    "message_id": msg.message_id,
                    "brainrot_name": msg.brainrot_name,
                    "generation_rate": msg.generation_rate,
                    "job_id": msg.job_id,
                    "channel_id": msg.channel_id,
                    "timestamp": msg.timestamp,
                    "players": msg.players,
                    "base_name": msg.base_name
                }
                for msg in all_notifications
            ],
            "message": response_message
        }
        
    except Exception as e:
        print(f"❌ Erro no endpoint /api/messages/new: {e}")
        return {
            "success": False,
            "new_messages": [],
            "message": f"Erro interno: {str(e)}"
        }

@app.get("/api/channels")
async def get_channels_info():
    """Endpoint para obter informações sobre os canais sendo monitorados - COMPATÍVEL COM LUA"""
    channel_info = []
    
    print(f"🔍 Obtendo informações de {len(DISCORD_CHANNELS)} canais...")
    
    for channel_id in DISCORD_CHANNELS:
        print(f"📡 Testando canal: {channel_id}")
        
        messages = fetch_discord_messages(channel_id)
        
        if messages is None:
            status = "error"
            message_count = 0
            error_msg = "Falha ao acessar canal"
        else:
            status = "online"
            message_count = len(messages)
            error_msg = None
        
        channel_info.append({
            "channel_id": channel_id,
            "status": status,
            "messages_available": message_count,
            "processed_messages": len(processed_messages[channel_id]),
            "error": error_msg
        })
        
        print(f"   📊 Status: {status}, Mensagens: {message_count}")
    
    return {
        "success": True,
        "channels": channel_info,
        "total_channels": len(DISCORD_CHANNELS),
        "message": f"Monitorando {len(DISCORD_CHANNELS)} canais do Discord"
    }

@app.get("/api/test")
async def test_endpoint():
    """Endpoint de teste com dados de exemplo - COMPATÍVEL COM LUA"""
    print("🧪 Gerando dados de teste...")
    
    test_data = [
        {
            "message_id": "test_123456789",
            "brainrot_name": "Los Tipi Tacos",
            "generation_rate": "2M",
            "job_id": "5ab7c5e4-35a1-4552-8264-4cbdd6aab1f6",
            "channel_id": DISCORD_CHANNELS[0],
            "timestamp": datetime.utcnow().isoformat(),
            "players": "7/8",
            "base_name": "Benzema12709"
        },
        {
            "message_id": "test_123456790",
            "brainrot_name": "Bambu Bambu Sahur",
            "generation_rate": "17M",
            "job_id": "6bc8d6f5-46b2-5663-9375-5dcee7bbcf2g7",
            "channel_id": DISCORD_CHANNELS[1],
            "timestamp": datetime.utcnow().isoformat(),
            "players": "6/8",
            "base_name": "OutraBase"
        }
    ]
    
    print(f"✅ Dados de teste gerados: {len(test_data)} notificações")
    
    return {
        "success": True,
        "new_messages": test_data,
        "message": "Dados de teste no formato compatível"
    }

@app.get("/api/debug/clear-cache")
async def clear_cache():
    """Endpoint para limpar o cache de mensagens processadas"""
    for channel_id in DISCORD_CHANNELS:
        processed_messages[channel_id].clear()
    
    return {
        "success": True,
        "message": f"Cache limpo para {len(DISCORD_CHANNELS)} canais",
        "cleared_channels": DISCORD_CHANNELS
    }

@app.get("/api/network")
async def network_info():
    """Endpoint para mostrar informações de rede"""
    network_info = get_network_info()
    return {
        "success": True,
        "network": network_info,
        "access_urls": {
            "local_access": f"http://{network_info['local_ip']}:8000",
            "public_access": f"http://{network_info['public_ip']}:8000" if network_info['public_ip'] != "Não disponível" else "Não disponível",
            "ngrok_url": ngrok_url,
            "all_network_ips": [f"http://{ip}:8000" for ip in network_info['network_ips']]
        },
        "ngrok_available": network_info['ngrok_available'],
        "ngrok_path": NGROK_PATH,
        "instructions": "Use o URL local para acesso na mesma rede. Para acesso externo, use ngrok."
    }

@app.get("/api/health")
async def health_check():
    """Health check da API"""
    network_info = get_network_info()
    return {
        "status": "online", 
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Discord Brainrot Notifications API",
        "channels_monitored": len(DISCORD_CHANNELS),
        "channels": DISCORD_CHANNELS,
        "cache_size": {channel_id: len(messages) for channel_id, messages in processed_messages.items()},
        "network": network_info,
        "ngrok_url": ngrok_url,
        "ngrok_available": network_info['ngrok_available']
    }

@app.get("/")
async def root():
    network_info = get_network_info()
    
    response = {
        "message": "Discord Brainrot Notifications API", 
        "status": "online",
        "channels": len(DISCORD_CHANNELS),
        "access_urls": {
            "local": f"http://{network_info['local_ip']}:8000",
            "public": f"http://{network_info['public_ip']}:8000" if network_info['public_ip'] != "Não disponível" else "Não disponível",
            "ngrok": ngrok_url
        },
        "ngrok_available": network_info['ngrok_available'],
        "endpoints": {
            "/api/messages/new": "Buscar novas mensagens",
            "/api/channels": "Informações dos canais", 
            "/api/test": "Dados de teste",
            "/api/health": "Status da API",
            "/api/network": "Informações de rede",
            "/api/debug/clear-cache": "Limpar cache"
        }
    }
    
    if not network_info['ngrok_available']:
        response["ngrok_instructions"] = "Para acesso externo, baixe ngrok de: https://ngrok.com/download"
    
    return response

# Testar permissões ao iniciar a API
@app.on_event("startup")
async def startup_event():
    print("🚀 Iniciando Discord Brainrot Notifications API...")
    print(f"📡 Monitorando {len(DISCORD_CHANNELS)} canais:")
    for i, channel_id in enumerate(DISCORD_CHANNELS, 1):
        print(f"   {i}. {channel_id}")
    
    # Verificar se ngrok está disponível
    ngrok_available = os.path.exists(NGROK_PATH)
    
    if ngrok_available:
        print(f"✅ Ngrok encontrado em: {NGROK_PATH}")
        # Iniciar ngrok em thread separada para não bloquear a inicialização
        def start_ngrok_async():
            global ngrok_url
            ngrok_url = start_ngrok_tunnel()
        
        ngrok_thread = threading.Thread(target=start_ngrok_async, daemon=True)
        ngrok_thread.start()
    else:
        print(f"❌ Ngrok não encontrado em: {NGROK_PATH}")
        print("📥 Para acesso externo, baixe de: https://ngrok.com/download")
    
    # Obter e mostrar informações de rede
    network_info = get_network_info()
    print("\n🌐 INFORMAÇÕES DE REDE:")
    print(f"   🖥️  Hostname: {network_info['hostname']}")
    print(f"   📍 IP Local: {network_info['local_ip']}")
    print(f"   🌍 IP Público: {network_info['public_ip']}")
    
    print("\n🔗 URLs DE ACESSO:")
    print(f"   💻 Local: http://{network_info['local_ip']}:8000")
    
    if ngrok_url:
        print(f"   🌍 Ngrok (QUALQUER LUGAR): {ngrok_url}")
        print("   ✅ Use este URL para acesso global!")
    elif ngrok_available:
        print("   ⏳ Ngrok iniciando... aguarde alguns segundos")
        print("   💡 Acesse /api/network para ver a URL")
    else:
        print("   ❌ Ngrok não disponível para acesso externo")
    
    if network_info['public_ip'] != "Não disponível":
        print(f"   🌐 Internet: http://{network_info['public_ip']}:8000")
        print("   ⚠️  Precisa de port forwarding no roteador")
    
    print("\n📝 INSTRUÇÕES:")
    if ngrok_url:
        print("   Para acesso de QUALQUER LUGAR, use o URL ngrok acima")
    else:
        print("   Para acesso local, use o IP local acima")
        print("   Para acesso externo, configure ngrok ou port forwarding")
    
    # Testar permissões do bot
    test_bot_permissions()

# Registrar função para parar ngrok ao sair
atexit.register(stop_ngrok_tunnel)

if __name__ == "__main__":
    import uvicorn
    print("🌐 Iniciando servidor FastAPI...")
    uvicorn.run(
        app, 
        host="0.0.0.0",  # Aceita conexões de qualquer IP
        port=8000, 
        log_level="info"
    )