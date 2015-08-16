@REM wrapper para llamar al ejecutable Python que lleva el control del juego
@echo off

@REM activar Virtualenv
call venv-win\Scripts\activate

@REM invocar script Python
python src\player.py %* > out.txt
