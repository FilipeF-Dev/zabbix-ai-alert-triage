#!/bin/sh
# Chamado pelo Zabbix (tipo de midia "Script"), parametro {EVENT.ID}.
# So grava o ID na fila e sai: a analise roda no servico triage, sem
# segurar o alerter do Zabbix.
case "$1" in
  ''|*[!0-9]*) echo "uso: $0 <eventid numerico>" >&2; exit 1 ;;
esac
printf '%s\n' "$1" > "/var/spool/triage/$1.evento.tmp" &&
  mv "/var/spool/triage/$1.evento.tmp" "/var/spool/triage/$1.evento"
