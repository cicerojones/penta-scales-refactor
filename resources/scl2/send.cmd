** send cmd

! send.cmd
echo Download tuning to a synthesizer
! First set the kind using SET SYNTHESIZER.
! This command file requires a MIDI file player.
!
send/file sysex.mid
!spawn/detached open sysex.mid
spawn/detached "/Applications/Sysex Librarian.app/Contents/MacOS/SysEx Librarian" sysex.mid
