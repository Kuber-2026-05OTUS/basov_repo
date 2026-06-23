# E. kubernetes-security
# Методическое пособие по выполнению домашнего задания курса «Инфраструктурная платформа на основе Kubernetes»

## Настройка сервисных аккаунтов и ограничение прав для них

---

## Содержание

1. Введение — 3  
2. Цели домашнего задания — 4  
3. Описание домашнего задания — 5  
4. Пошаговая инструкция выполнения домашнего задания — 7  
5. Сдача задания — 8  
6. Критерии оценки — 9  
7. Рекомендуемые источники — 10  

---

## 1. Введение

### Service Account

Вид учетной записи, предназначенный для внутрикластерных процессов, запущенных в Pod-ах вашего кластера, которым необходимо получить доступ к API кластера.  
По умолчанию, если не указано, поды запускаются с дефолтным сервисным аккаунтом — мы будем создавать свои SA и запускать поды под ними.

### Roles и ClusterRoles

Определяют набор прав доступа к определенным типам объектов и ресурсам на уровне пространства имен и на уровне всего кластера соответственно.

### RoleBindings и ClusterRoleBindings

Определяют связь между ServiceAccount и ролью на уровне пространства имен или всего кластера соответственно.  
В задании мы будем использовать оба типа связей.

---

## 2. Цели домашнего задания

- Получить представление о объекте ServiceAccount, его роли в ЖЦ подов.  
- Научиться настраивать bindings для ServiceAccount с различными правами: на уровне namespace так и на уровне всего кластера.  
- Понять механизм работы секретов, которые создаются для SA.

---

## 3. Описание домашнего задания

В данном домашнем задании вы научитесь создавать service account, настраивать их права в рамках одного namespace и кластера целиком.

### Подготовка к выполнению домашнего задания

- Создать branch `kubernetes-security` — данное домашнее задание будет выполняться в этой ветке.  
- Создать папку `kubernetes-security` — все файлы, которые у вас получаются во время выполнения данного ДЗ, необходимо поместить в эту папку.

### Рекомендуемые источники

- Документация по service account https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/ , roles https://kubernetes.io/docs/concepts/security/service-accounts/ и role bindings  https://kubernetes.io/docs/reference/access-authn-authz/rbac/
- Документация по kubeconfig  https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/
- Посмотреть содержимое сгенерированного токена и его expiration time можно, например, по ссылке:  
  https://kubernetes.io/docs/tasks/access-application-cluster/create-authorization-token/
  
---

## 4. Пошаговая инструкция выполнения домашнего задания

1. В namespace `homework` создать service account `monitoring` и дать ему доступ к эндпоинту `/metrics` вашего кластера.  
2. Изменить манифест deployment из прошлых ДЗ так, чтобы поды запускались под service account `monitoring`.  
3. В namespace `homework` создать service account с именем `cd` и дать ему роль `admin` в рамках namespace `homework`.  
4. Создать kubeconfig для service account `cd`.  
5. Сгенерировать для service account `cd` токен с временем действия 1 день и сохранить его в файл `token`.

### Задание с *

Модифицировать deployment из прошлых ДЗ так, чтобы в процессе запуска pod происходило обращение к эндпоинту `/metrics` вашего кластера (механика вызова не принципиальна), результат ответа сохранялся в файл `metrics.html`, и содержимое этого файла можно было бы получить при обращении по адресу `/metrics.html` вашего сервиса.

---

## 5. Сдача задания

- Добавить все получившиеся файлы в ветку `kubernetes-security`.  
- Создать Pull Request к ветке `master`.  
- Заполнить описание PR по шаблону.  
- Не мерджить PR самостоятельно.  
- Если у вас возникли вопросы при выполнении ДЗ и необходима консультация преподавателей — добавьте к PR метку `Review Required`.  
- В личном кабинете Otus сдать ДЗ на проверку, указав ссылку на Pull Request.

---

## 6. Критерии оценки

| Баллы | Описание |
|-------|----------|
| 0     | Задание не выполнено или выполнено не полностью |
| 1     | Выполнены полностью все основные задания |
| 2     | Выполнены полностью также все задания с * |

---

## 7. Рекомендуемые источники

- Документация по service account https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/ , roles https://kubernetes.io/docs/concepts/security/service-accounts/ и role bindings  https://kubernetes.io/docs/reference/access-authn-authz/rbac/
- Документация по kubeconfig  https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/
- Посмотреть содержимое сгенерированного токена и его expiration time можно, например, по ссылке:  
  https://kubernetes.io/docs/tasks/access-application-cluster/create-authorization-token/
