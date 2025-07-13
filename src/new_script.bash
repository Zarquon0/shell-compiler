echo "abc\\ndef" | ./monitor-components/monitor -d monitor-components/sdfa-aaaca133.bc | grep "def" | ./monitor-components/monitor -d monitor-components/sdfa-aaaca133.bc
( echo "abc\\ndef" | ./monitor-components/monitor -d monitor-components/sdfa-aaaca133.bc | grep "def" | ./monitor-components/monitor -d monitor-components/sdfa-aaaca133.bc
                ls )
