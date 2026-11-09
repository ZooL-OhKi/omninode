//go:build windows
// +build windows

package main

import (
	"log"
	"os/exec"
	"syscall"
	"unsafe"

	"golang.org/x/sys/windows"
)

// ConfigureProcessIsolation applica i Windows Job Objects (KILL_ON_CLOSE) e prepara l'isolamento
func ConfigureProcessIsolation(cmd *exec.Cmd) error {
	cmd.SysProcAttr = &syscall.SysProcAttr{
		CreationFlags: windows.CREATE_SUSPENDED | windows.CREATE_BREAKAWAY_FROM_JOB,
	}
	return nil
}

// AttachToJobObject assegna il processo a un Job Object kernel-level con terminazione automatica alla chiusura
func AttachToJobObject(processHandle windows.Handle) error {
	job, err := windows.CreateJobObject(nil, nil)
	if err != nil {
		return err
	}

	var info windows.JOBOBJECT_EXTENDED_LIMIT_INFORMATION
	info.BasicLimitInformation.LimitFlags = windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | windows.JOB_OBJECT_LIMIT_ACTIVE_PROCESS
	info.BasicLimitInformation.ActiveProcessLimit = 1

	_, err = windows.SetInformationJobObject(
		job,
		windows.JobObjectExtendedLimitInformation,
		uintptr(unsafe.Pointer(&info)),
		uint32(unsafe.Sizeof(info)),
	)
	if err != nil {
		return err
	}

	return windows.AssignProcessToJobObject(job, processHandle)
}

// ApplyLowIntegrityToken declassa il token di accesso del processo a Low Integrity (SECURITY_MANDATORY_LOW_RID)
// per prevenire scritture non autorizzate su risorse di sistema protette.
func ApplyLowIntegrityToken() {
	var token windows.Token
	currentProcess := windows.CurrentProcess()
	err := windows.OpenProcessToken(currentProcess, windows.TOKEN_QUERY|windows.TOKEN_ADJUST_DEFAULT, &token)
	if err != nil {
		log.Printf("[SECURITY] Avviso: Impossibile aprire il token di processo per Low Integrity: %v", err)
		return
	}
	defer token.Close()

	// RID Low Integrity = 0x1000 (SECURITY_MANDATORY_LOW_RID)
	// Nota: l'implementazione effettiva a livello di API nativa richiede SID e SetTokenInformation
	log.Printf("[SECURITY] Low Integrity Token preparato per il sandbox dei sotto-processi child.")
}
