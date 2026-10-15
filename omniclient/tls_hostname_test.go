package main

import (
	"context"
	"crypto/rand"
	"crypto/rsa"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"errors"
	"io"
	"math/big"
	"net"
	"os"
	"path/filepath"
	"testing"
	"time"
)

const testTLSTimeout = 3 * time.Second

func writeTestCertificate(t *testing.T, dir, name string, der []byte, key *rsa.PrivateKey) (certPath, keyPath string) {
	t.Helper()
	certPath = filepath.Join(dir, name+".crt")
	keyPath = filepath.Join(dir, name+".key")

	certPEM := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})
	keyDER, err := x509.MarshalPKCS8PrivateKey(key)
	if err != nil {
		t.Fatal(err)
	}
	keyPEM := pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: keyDER})

	if err := os.WriteFile(certPath, certPEM, 0o600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(keyPath, keyPEM, 0o600); err != nil {
		t.Fatal(err)
	}
	return certPath, keyPath
}

func TestBuildTLSConfigRejectsHostnameMismatch(t *testing.T) {
	dir := t.TempDir()
	ctx, cancel := context.WithTimeout(context.Background(), testTLSTimeout)
	defer cancel()

	caKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		t.Fatal(err)
	}
	caTemplate := &x509.Certificate{
		SerialNumber:          big.NewInt(1),
		Subject:               pkix.Name{CommonName: "OmniNode Test CA"},
		NotBefore:             time.Now().Add(-time.Minute),
		NotAfter:              time.Now().Add(time.Hour),
		KeyUsage:              x509.KeyUsageCertSign | x509.KeyUsageDigitalSignature,
		BasicConstraintsValid: true,
		IsCA:                  true,
	}
	caDER, err := x509.CreateCertificate(rand.Reader, caTemplate, caTemplate, &caKey.PublicKey, caKey)
	if err != nil {
		t.Fatal(err)
	}
	caCert, err := x509.ParseCertificate(caDER)
	if err != nil {
		t.Fatal(err)
	}
	caPath, _ := writeTestCertificate(t, dir, "ca", caDER, caKey)

	serverKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		t.Fatal(err)
	}
	serverTemplate := &x509.Certificate{
		SerialNumber: big.NewInt(2),
		Subject:      pkix.Name{CommonName: "broker.omninode.local"},
		NotBefore:    time.Now().Add(-time.Minute),
		NotAfter:     time.Now().Add(time.Hour),
		KeyUsage:     x509.KeyUsageDigitalSignature | x509.KeyUsageKeyEncipherment,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
		DNSNames:     []string{"broker.omninode.local"},
	}
	serverDER, err := x509.CreateCertificate(rand.Reader, serverTemplate, caCert, &serverKey.PublicKey, caKey)
	if err != nil {
		t.Fatal(err)
	}
	serverCertPath, serverKeyPath := writeTestCertificate(t, dir, "server", serverDER, serverKey)

	clientKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		t.Fatal(err)
	}
	clientTemplate := &x509.Certificate{
		SerialNumber: big.NewInt(3),
		Subject:      pkix.Name{CommonName: "worker-1"},
		NotBefore:    time.Now().Add(-time.Minute),
		NotAfter:     time.Now().Add(time.Hour),
		KeyUsage:     x509.KeyUsageDigitalSignature | x509.KeyUsageKeyEncipherment,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth},
	}
	clientDER, err := x509.CreateCertificate(rand.Reader, clientTemplate, caCert, &clientKey.PublicKey, caKey)
	if err != nil {
		t.Fatal(err)
	}
	clientCertPath, clientKeyPath := writeTestCertificate(t, dir, "client", clientDER, clientKey)

	tlsConfig, err := buildTLSConfig(caPath, clientCertPath, clientKeyPath, "wrong.host.example")
	if err != nil {
		t.Fatal(err)
	}
	if tlsConfig.ServerName != "wrong.host.example" {
		t.Fatalf("unexpected ServerName: %s", tlsConfig.ServerName)
	}
	if tlsConfig.MinVersion != tls.VersionTLS13 || tlsConfig.MaxVersion != tls.VersionTLS13 {
		t.Fatal("expected TLS 1.3 only")
	}
	if tlsConfig.InsecureSkipVerify {
		t.Fatal("certificate verification must not be skipped")
	}

	serverTLS := &tls.Config{
		Certificates: []tls.Certificate{{
			Certificate: [][]byte{serverDER},
			PrivateKey:  serverKey,
		}},
		ClientAuth: tls.RequireAndVerifyClientCert,
		ClientCAs:  x509.NewCertPool(),
		MinVersion: tls.VersionTLS13,
		MaxVersion: tls.VersionTLS13,
	}
	if !serverTLS.ClientCAs.AppendCertsFromPEM(mustPEM(caDER)) {
		t.Fatal("failed to load test CA")
	}

	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()

	serverDone := make(chan struct{})
	go func() {
		defer close(serverDone)
		for {
			conn, err := listener.Accept()
			if err != nil {
				return
			}
			go func(rawConn net.Conn) {
				defer rawConn.Close()
				tlsConn := tls.Server(rawConn, serverTLS)
				tlsConn.SetDeadline(time.Now().Add(testTLSTimeout))
				if err := tlsConn.HandshakeContext(ctx); err != nil {
					return
				}
				_, _ = io.Copy(io.Discard, tlsConn)
			}(conn)
		}
	}()

	dialer := &net.Dialer{Timeout: testTLSTimeout}
	rawConn, err := dialer.DialContext(ctx, "tcp", listener.Addr().String())
	if err != nil {
		t.Fatalf("dial failed before TLS handshake: %v", err)
	}
	defer rawConn.Close()

	clientTLS := tls.Client(rawConn, tlsConfig)
	clientTLS.SetDeadline(time.Now().Add(testTLSTimeout))
	handshakeErr := clientTLS.HandshakeContext(ctx)

	if handshakeErr == nil {
		t.Fatal("expected hostname mismatch rejection")
	}
	var hostnameError *x509.HostnameError
	if !errors.As(handshakeErr, &hostnameError) {
		t.Fatalf("expected x509 hostname error, got: %v", handshakeErr)
	}

	select {
	case <-serverDone:
	case <-ctx.Done():
		t.Fatal("test timed out waiting for TLS server")
	}
}

func mustPEM(der []byte) []byte {
	return pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})
}
