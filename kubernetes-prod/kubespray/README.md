# Задание с * — HA-кластер через kubespray

Отдельный набор из минимум 5 ВМ (3 master + минимум 2 worker), не тот же
кластер, что в основном задании.

## Как запустить

```bash
git clone --branch release-2.26 https://github.com/kubernetes-sigs/kubespray.git
cd kubespray
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp -rfp inventory/sample inventory/otus-prod
cp ../inventory/hosts.yaml inventory/otus-prod/hosts.yaml   # файл из этой папки, отредактированный под ваши реальные IP

ansible-playbook -i inventory/otus-prod/hosts.yaml \
  --become --become-user=root \
  -u <ssh-user> --private-key ~/.ssh/<key> \
  cluster.yml
```

После завершения плейбука настройте `kubectl` с любого master-узла
(kubeconfig лежит в `/etc/kubernetes/admin.conf`) и проверьте:

```bash
kubectl get nodes -o wide
```

Ожидаемый результат: 3 узла с ролью `control-plane` и минимум 2 узла с
ролью `worker`, все в статусе `Ready`.

## Ограничение этой песочницы

`inventory/hosts.yaml` в этой папке — рабочий шаблон inventory для 3
master + 2 worker с реальными полями (`ansible_host`, `ip`,
`access_ip`), но с IP-адресами-плейсхолдерами (`10.0.0.11` и т.д.),
потому что для реального запуска `ansible-playbook` нужны 5 живых ВМ по
SSH, а их в этой сборочной песочнице нет. См.
`../IMPLEMENTATION_REPORT.md` за подробностями, что проверено, а что нет.
