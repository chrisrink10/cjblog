#!/usr/bin/env bash

####
# Automate the process of creating OpenSSL certificates
#
# Last Updated: Dec 30, 2016
####

# Help text
GENKEY_USAGE="usage: sudo ./gen-key.sh [-h] [--self-signed] [site] [bits]"

# Defaults
HOSTNAME=$(hostname)
SSL_BITS=2048

# Check if we're being asked for help
if [[ $1 == "-h" ]]
then
	echo $GENKEY_USAGE
	exit 1
fi

# Allow users to self-sign
if [[ $1 == "--self-signed" ]]
then
	SELF_SIGNED=1
	GENKEY_SITE=${2:-$HOSTNAME}
	GENKEY_BITS=${3:-$SSL_BITS}
else
	SELF_SIGNED=0
	GENKEY_SITE=${1:-$HOSTNAME}
	GENKEY_BITS=${2:-$SSL_BITS}
fi

# Get a few things together
if [ -z "$GENKEY_BITS" ] || [ $GENKEY_BITS -lt 2 ] || [ $(( $GENKEY_BITS % 2 )) -ne 0 ]
then
	echo "error: bits must be greater than 0 and a factor of 2"
	echo $GENKEY_USAGE
	exit 1
fi

# Check for sudo
user=$(whoami)
if [[ $user != "root" ]]
then
	echo "error: must be root"
	echo $GENKEY_USAGE
	exit 1
fi

# Create an RSA private key
echo "Generating RSA private key..."
openssl genrsa -out $GENKEY_SITE.key $GENKEY_BITS
echo "Success!"

# Generate a certificate signing request
echo ""
echo "Generating certificate signing request..."
openssl req -new -sha256 -key $GENKEY_SITE.key -out $GENKEY_SITE.csr
echo "Success!"
echo "Using the value of the certificate signing request, generate a public key."
echo "The contents of the CSR are given below:"

# IF the user wants to self-sign, perform that for them
if [[ $SELF_SIGNED == 1 ]]
then
	echo "Self-signing your certificate..."
	openssl x509 -req -days 365 -in $GENKEY_SITE.csr -signkey $GENKEY_SITE.key -out $GENKEY_SITE.crt
else
	# Print the CSR to have it signed
	echo "Using the value of the certificate signing request, generate a public key."
	echo "The contents of the CSR are given below:"
	cat $GENKEY_SITE.csr

	# Get the user's response (PEM public key)
	echo ""
	echo "Now, enter the contents of the public key below:"
	while IFS=$'' read -r LINE && [[ -n "$LINE" ]]; do
        	echo "$LINE" >> "$GENKEY_SITE.pem.partial"
	done
	echo "Success! You have now generated an SSL key-value pair."
fi

# Produce the DH parameter file too
echo ""
read -p "Press any key to generate Diffie-Hellman parameters." -n 1
openssl dhparam -out $GENKEY_SITE.dhparam.pem $GENKEY_BITS

# Inform the user about the certificate chain
if [[ $SELF_SIGNED == 0 ]]
then
	# Advise the user on some other info
        echo ""
        echo "You will want to provide any intermediate CA certificates in your chain."
        echo "Your root certificate authority should provide you with any intermediate"
        echo "certificates. Download these and perform a command such as:"
        echo ""
        echo "    cat $GENKEY_SITE.pem.partial [CACert.pem] > $GENKEY_SITE.pem"
        echo ""
        echo "This will make sure that clients know the full SSL Certificate chain from"
        echo "your server and are not forced to get it themselves."
fi