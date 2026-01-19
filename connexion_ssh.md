# Connexion SSH entre un PC et un Raspberry Pi via USB-C

Ce guide explique comment établir une connexion SSH entre un ordinateur (PC) et un Raspberry Pi en utilisant un câble USB-C configuré comme interface réseau (USB gadget Ethernet).

---

## 1. Prérequis matériels

- Raspberry Pi compatible USB gadget (Pi 4 dans notre cas)
- Carte micro-SD avec Raspberry Pi OS
- Câble USB-C ↔ USB (PC)
- Un PC sous Linux (NetworkManager installé)

---

## 2. Préparation de la carte SD (côté PC)

### 2.1 Activer le mode USB gadget

#### Fichier `config.txt`
Dans `boot/config.txt`, ajouter : **dtoverlay=dwc2**


#### Fichier `cmdline.txt`
Dans `boot/cmdline.txt`, ajouter **modules-load=dwc2,g_ether** après `rootwait`


⚠️ Tout doit rester sur **une seule ligne**.

---

## 3. Démarrage initial du Raspberry Pi

1. Insérer la carte SD dans le Raspberry Pi
2. Brancher le câble USB-C entre le Pi et le PC
3. Alimenter le Pi (via le même câble USB)

---

## 4. Configuration réseau côté Raspberry Pi

### 4.1 Vérifier la présence de l’interface USB

Sur le Raspberry Pi :
```bash
ip a
```

Une interface usb0 doit apparaître.

### 4.2 Assigner une IP statique à usb0 (NetworkManager)
```bash
sudo nmcli connection add \
  type ethernet \
  ifname usb0 \
  con-name usb-usb \
  ip4 192.168.7.2/24
```

Activer la connexion :
```bash
sudo nmcli connection up usb-usb
```

Vérification :
```bash
ip a show usb0
```

Résultat attendu : `inet 192.168.7.2/24`

## 5. Vérification et activation du service SSH (côté Pi)
### 5.1 Vérifier que SSH est installé

```bash
which sshd
```

Si absent :
```bash
sudo apt update
sudo apt install openssh-server
```

### 5.2 Activer et démarrer SSH
```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

Vérification :
```bash
sudo systemctl status ssh
```

## 6. Configuration réseau côté PC

## 7. Test de la connexion réseau

Depuis le PC :
```bash
ping 192.168.7.2
```

## 8. Connexion SSH finale

Depuis le PC :
```bash
ssh pi@192.168.7.2
```
