#!/bin/bash
echo "abc\ndef" | grep "def"
(
    echo "abc\ndef" | grep "def"
    ls
)