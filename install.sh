#!/bin/sh
# Instala o Triagem IA no servidor do Zabbix (Ubuntu/Debian).
#
# Uso (na VM, depois do scp para /tmp/triage):
#   sudo sh /tmp/triage/instalar-triage.sh
#
# Pode rodar de novo sem estrago: atualiza programa e base, NUNCA sobrescreve
# /etc/triage/triage.conf se ele ja existir, e NAO liga o servico (passo 7).
set -eu

ORIGEM=/tmp/triage
SDK_VERSAO=2.5.0   # versao testada

[ "$(id -u)" -eq 0 ] || { echo "rode com sudo"; exit 1; }
for f in triage.py BASE-CONHECIMENTO.md triage-enqueue.sh triage.service triage.conf.example; do
  [ -f "$ORIGEM/$f" ] || { echo "falta $ORIGEM/$f (refazer o scp)"; exit 1; }
done
id zabbix >/dev/null 2>&1 || { echo "usuario zabbix nao existe?"; exit 1; }

echo "== 1/6 pacotes"
apt-get install -y python3-venv >/dev/null

echo "== 2/6 pastas"
mkdir -p /opt/triage /etc/triage /var/spool/triage/feitos /var/spool/triage/falhos /var/log/triage

echo "== 3/6 programa e base"
install -m 644 "$ORIGEM/triage.py" "$ORIGEM/BASE-CONHECIMENTO.md" /opt/triage/
[ -x /opt/triage/venv/bin/python ] || python3 -m venv /opt/triage/venv
/opt/triage/venv/bin/pip install -q "anthropic==$SDK_VERSAO"
/opt/triage/venv/bin/python -m py_compile /opt/triage/triage.py
echo "   SINTAXE-OK, SDK $(/opt/triage/venv/bin/python -c 'import anthropic;print(anthropic.__version__)')"

echo "== 4/6 script de alerta"
DIR=$(sed -n 's/^AlertScriptsPath=//p' /etc/zabbix/zabbix_server.conf | tail -1)
[ -n "$DIR" ] || DIR=/usr/lib/zabbix/alertscripts
mkdir -p "$DIR"
install -m 755 "$ORIGEM/triage-enqueue.sh" "$DIR/"
echo "   $DIR/triage-enqueue.sh"

echo "== 5/6 configuracao"
if [ -f /etc/triage/triage.conf ]; then
  echo "   /etc/triage/triage.conf ja existe: mantido"
else
  install -m 600 "$ORIGEM/triage.conf.example" /etc/triage/triage.conf
  echo "   criado a partir do exemplo"
fi
chown -R zabbix:zabbix /var/spool/triage /var/log/triage /etc/triage
chmod 600 /etc/triage/triage.conf

echo "== 6/6 servico"
install -m 644 "$ORIGEM/triage.service" /etc/systemd/system/triage.service
systemctl daemon-reload
# ja ligado: reinicia para carregar o programa novo; desligado: continua desligado
if systemctl is-active --quiet triage; then
  systemctl restart triage && echo "   estava ligado: reiniciado com o programa novo"
else
  echo "   copiado, NAO ligado (ligar no passo 7)"
fi

# teste de escrita na fila como o usuario do Zabbix
sudo -u zabbix "$DIR/triage-enqueue.sh" 999999999 && rm -f /var/spool/triage/999999999.evento \
  && echo "   fila gravavel pelo zabbix: OK"

FALTA=$(grep -c 'COLE_AQUI' /etc/triage/triage.conf || true)
echo
if [ "$FALTA" -gt 0 ]; then
  echo "PRONTO, falta preencher $FALTA COLE_AQUI:  sudo nano /etc/triage/triage.conf"
else
  echo "PRONTO. Configuracao preenchida. Proximo: triage.py analisar 0 --sem-email"
fi
