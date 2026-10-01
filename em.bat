@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================================
:: stratigraph-templates - Quick Commands (Windows)
::
:: The same commands as em.sh, with the same help. Every command runs
::     .venv\Scripts\python.exe -m stratigraph_templates.cli ...
:: so it works even when the console script is missing. The reports
:: (status, after-bump) are tools\em_report.py, shared with em.sh.
:: Nothing here commits or pushes.
:: ============================================================================

cd /d "%~dp0"
set "ROOT=%~dp0"
set "PY=%ROOT%.venv\Scripts\python.exe"
if "%STRATIGRAPH_S3DGRAPHY_SRC%"=="" (
    set "S3D_SRC=%ROOT%..\s3Dgraphy\src"
) else (
    set "S3D_SRC=%STRATIGRAPH_S3DGRAPHY_SRC%"
)

set "CMD=%~1"
if "%CMD%"=="" goto :help
if "%CMD%"=="help" goto :help
if "%CMD%"=="-h" goto :help
if "%CMD%"=="--help" goto :help
if "%CMD%"=="setup" goto :setup
if "%CMD%"=="snapshot" goto :snapshot
if "%CMD%"=="validate" goto :passthru
if "%CMD%"=="build" goto :passthru
if "%CMD%"=="info" goto :passthru
if "%CMD%"=="print" goto :passthru
if "%CMD%"=="form" goto :passthru
if "%CMD%"=="vocab" goto :passthru
if "%CMD%"=="cli" goto :cli
if "%CMD%"=="after-bump" goto :after_bump
if "%CMD%"=="test" goto :test
if "%CMD%"=="status" goto :status
echo unknown command '%CMD%'
echo.
goto :overview

:: ----------------------------------------------------------------------------
:help
if "%~2"=="" goto :overview
:: The long help lives in em.sh, once. On Windows it is read from there, so
:: the two cannot drift; Git for Windows ships the bash that prints it.
where bash >nul 2>&1
if errorlevel 1 (
    echo The long help of '%~2' is in em.sh ^(function help_%~2^): open it, or
    echo install Git for Windows and run: bash em.sh help %~2
    exit /b 0
)
bash "%ROOT%em.sh" help %~2
exit /b %errorlevel%

:overview
echo stratigraph-templates - em.bat ^<command^> [args]
echo.
echo Recording sheets are DATA, compiled against a SNAPSHOT of s3Dgraphy's
echo datamodel. These commands wrap the CLI, pytest and pip the repository
echo already uses. Nothing here commits or pushes.
echo.
echo   setup                 Create or repair .venv (python ^>= 3.11, pip install -e .[dev]).
echo                           em.bat setup
echo   snapshot              Re-take registry\s3dgraphy-snapshot.json from s3Dgraphy; show the diff.
echo                           em.bat snapshot
echo   validate [ids...]     Check the definitions (shape + graph bindings).
echo                           em.bat validate iccd-us-2021
echo   build [ids...]        Compile to dist\schede\^<id^>\^<version^>.json + index.json.
echo                           em.bat build
echo   after-bump            snapshot -^> validate -^> build, stop at the first error,
echo                         list the schede whose compiled output changed.
echo                           em.bat after-bump
echo   info ^<id^>             The numbers of one definition.
echo                           em.bat info iccd-us-2021
echo   print ^<id^> [args...]  A4 PDF (arguments go to the CLI).
echo                           em.bat print iccd-us-2021 --record examples\us-3014-demo.yaml --lang it -o out\us.pdf
echo   form ^<id^> [args...]   Fillable HTML form (arguments go to the CLI).
echo                           em.bat form iccd-us-2021 --record examples\us-3014-demo.yaml --lang it -o out\us.html
echo   vocab [args...]       List schemes, or resolve a concept label.
echo                           em.bat vocab --scheme fx-ue-definicion-es
echo   cli [args...]         Any other CLI subcommand, as is.
echo                           em.bat cli --help
echo   test [pytest args...] Run the test suite.
echo                           em.bat test -q
echo   status                Snapshot vs the s3Dgraphy next door: versions, fingerprint, files that differ.
echo                           em.bat status
echo   help [command]        This list, or the long help of one command (read from em.sh).
echo                           em.bat help after-bump
echo.
echo The usual day after a datamodel change in s3Dgraphy:
echo     em.bat status       (does the snapshot still match?)
echo     em.bat after-bump   (if not: re-snapshot, validate, build)
echo     git diff registry\ dist\    (review, then commit by hand)
exit /b 0

:: ----------------------------------------------------------------------------
:need_venv
if not exist "%PY%" (
    echo [ERROR] no .venv here ^(or it lost its interpreter^). Run: em.bat setup
    exit /b 1
)
"%PY%" -c "import stratigraph_templates" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] the .venv cannot import stratigraph_templates. Run: em.bat setup
    exit /b 1
)
exit /b 0

:: ----------------------------------------------------------------------------
:setup
set "BASEPY="
if exist "%PY%" (
    "%PY%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
    if not errorlevel 1 (
        echo Keeping .venv
        goto :setup_install
    )
    echo [WARN] .venv is broken or older than 3.11: recreating it
)
if not "%PYTHON%"=="" set "BASEPY=%PYTHON%"
if "!BASEPY!"=="" ( py -3.14 --version >nul 2>&1 && set "BASEPY=py -3.14" )
if "!BASEPY!"=="" ( py -3.13 --version >nul 2>&1 && set "BASEPY=py -3.13" )
if "!BASEPY!"=="" ( py -3.12 --version >nul 2>&1 && set "BASEPY=py -3.12" )
if "!BASEPY!"=="" ( py -3.11 --version >nul 2>&1 && set "BASEPY=py -3.11" )
if "!BASEPY!"=="" (
    echo [ERROR] no Python ^>= 3.11 found ^(pyproject: requires-python ^>= 3.11^).
    echo Install one from python.org, or: set PYTHON=C:\path\python.exe ^& em.bat setup
    exit /b 1
)
echo Using !BASEPY!
if exist ".venv" rmdir /s /q ".venv"
!BASEPY! -m venv .venv
if errorlevel 1 ( echo [ERROR] venv creation failed & exit /b 1 )
:setup_install
echo pip install -e .[dev]
"%PY%" -m pip install --quiet --upgrade pip
"%PY%" -m pip install --quiet -e ".[dev]"
if errorlevel 1 ( echo [ERROR] pip install failed - read the errors above & exit /b 1 )
"%PY%" -m stratigraph_templates.cli --help >nul
if errorlevel 1 ( echo [ERROR] the CLI does not answer after the install & exit /b 1 )
if exist ".venv\Scripts\stratigraph-templates.exe" (
    echo .venv ready: .venv\Scripts\stratigraph-templates.exe present, the CLI answers
) else (
    echo [WARN] the console script is missing - every em.bat command works anyway ^(python -m^)
)
exit /b 0

:: ----------------------------------------------------------------------------
:snapshot
call :need_venv || exit /b 1
call :do_snapshot
exit /b %errorlevel%

:do_snapshot
echo registry-snapshot from %S3D_SRC%
set "STRATIGRAPH_S3DGRAPHY_SRC=%S3D_SRC%"
"%PY%" -m stratigraph_templates.cli registry-snapshot
if errorlevel 1 exit /b 1
"%PY%" tools\em_report.py provenance
git diff --quiet -- registry/
if errorlevel 1 (
    git --no-pager diff --stat -- registry/
    echo [WARN] the snapshot changed: review git diff registry/ before you commit
) else (
    echo registry/ unchanged: the snapshot already said this
)
exit /b 0

:passthru
call :need_venv || exit /b 1
shift
set "ARGS="
:passthru_loop
if "%~1"=="" goto :passthru_run
set "ARGS=!ARGS! %1"
shift
goto :passthru_loop
:passthru_run
"%PY%" -m stratigraph_templates.cli %CMD% !ARGS!
exit /b %errorlevel%

:cli
call :need_venv || exit /b 1
set "ARGS=%*"
set "ARGS=!ARGS:~4!"
"%PY%" -m stratigraph_templates.cli !ARGS!
exit /b %errorlevel%

:after_bump
call :need_venv || exit /b 1
echo 1/3 snapshot
call :do_snapshot
if errorlevel 1 ( echo [ERROR] stopped at 1/3 snapshot & exit /b 1 )
echo 2/3 validate
"%PY%" -m stratigraph_templates.cli validate
if errorlevel 1 ( echo [ERROR] stopped at 2/3 validate ^(nothing built^) & exit /b 1 )
echo 3/3 build
"%PY%" -m stratigraph_templates.cli build
if errorlevel 1 ( echo [ERROR] stopped at 3/3 build & exit /b 1 )
echo.
echo schede whose compiled output changed (against the last commit):
"%PY%" tools\em_report.py changed
echo.
git status --short -- registry/ dist/
echo after-bump done - nothing committed. Review: git diff registry/ dist/
echo   next: em.bat test. tests\golden\iccd-us-2021.json records the s3dgraphy version too,
echo   so test_golden_iccd fails after every snapshot until you refresh it:
echo     set STRATIGRAPH_UPDATE_GOLDEN=1 ^& em.bat test tests/test_build.py::test_golden_iccd
exit /b 0

:test
call :need_venv || exit /b 1
set "ARGS=%*"
set "ARGS=!ARGS:~5!"
"%PY%" -m pytest !ARGS!
exit /b %errorlevel%

:status
call :need_venv || exit /b 1
echo snapshot   registry\s3dgraphy-snapshot.json
"%PY%" tools\em_report.py provenance
"%PY%" tools\em_report.py status "%S3D_SRC%"
set "RC=%errorlevel%"
git status --short -- registry/ dist/
exit /b %RC%
