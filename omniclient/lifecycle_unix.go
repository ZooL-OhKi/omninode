//go:build !windows
// +build !windows

package main

import (
	"os/exec"
	"syscall"
)

// ConfigureProcessIsolation imposta il process group separato su Unix per un graceful shutdown pulito
func ConfigureProcessIsolation(cmd *exec.Cmd) error {
	cmd.SysProcAttr = &syscall.SysProcAttr{
		Setpgid: true,
	}
	return nil
}
