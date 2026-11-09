package main

import (
	"errors"
	"fmt"
	"os"
	"strings"
)

const secretRefPrefix = "vault:"
const envRefPrefix = "env:"

func resolveAgentValue(text, secretRef string) (string, error) {
	if strings.TrimSpace(secretRef) != "" {
		return ResolveSecret(secretRef)
	}

	return text, nil
}

func ResolveSecret(reference string) (string, error) {
	reference = strings.TrimSpace(reference)
	if reference == "" {
		return "", errors.New("riferimento segreto vuoto")
	}

	switch {
	case strings.HasPrefix(reference, envRefPrefix):
		name := strings.TrimSpace(strings.TrimPrefix(reference, envRefPrefix))
		if name == "" {
			return "", errors.New("nome variabile d'ambiente mancante nel riferimento env:")
		}

		value := os.Getenv(name)
		if value == "" {
			return "", fmt.Errorf("variabile d'ambiente %q non impostata", name)
		}

		return value, nil

	case strings.HasPrefix(reference, secretRefPrefix):
		name := strings.TrimSpace(strings.TrimPrefix(reference, secretRefPrefix))
		if name == "" {
			return "", errors.New("nome segreto mancante nel riferimento vault:")
		}

		envName := "OMNINODE_SECRET_" + strings.ToUpper(strings.NewReplacer("-", "_", ".", "_", ":", "_").Replace(name))
		value := os.Getenv(envName)
		if value == "" {
			return "", fmt.Errorf("segreto %q non disponibile tramite variabile d'ambiente %q", name, envName)
		}

		return value, nil

	default:
		return "", fmt.Errorf("riferimento segreto non supportato: %q; usa vault:NAME oppure env:VARIABLE_NAME", reference)
	}
}

func MaskSecret(value string) string {
	if value == "" {
		return ""
	}

	if len(value) <= 4 {
		return "****"
	}

	return "****" + value[len(value)-4:]
}
