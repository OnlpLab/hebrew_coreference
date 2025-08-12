conda activate np
Write-Output "Python Running:"
which python

$baseUdFiles = "C:\Users\rafael\Desktop\studies\MSC\Theses\np_chunckers\heb_np_chuncker\corpus\UD_Hebrew-HTB\he_htb-ud-"
$outBase = "C:\Users\rafael\Desktop\studies\MSC\Theses\np_chunckers\heb_np_chuncker\np_data\gold_seg\ud_parse"

$udFiles = @("train.conllu", "dev.conllu", "test.conllu")
$nestOpt = @("flat", "nested")
$posOpt = @("no_possessive", "with_possessive")

Set-Location "C:\Users\rafael\Desktop\studies\MSC\Theses\np_chunckers\heb_np_chuncker\"
foreach ($pos in $posOpt)
{
    foreach ($nest in $nestOpt)
    {
        $newDir = -join ($outBase, "\", $pos, "\", $nest)
        Write-Output "Creating a new folder in:"
        Write-Output $newDir
        New-Item -Path $newDir -ItemType Directory
        foreach ($file in $udFiles)
        {
            $out_file = $file.split('\.')[-2]
            $output = (-join ($newDir, "\", $out_file, ".json"))
            $input = (-join ($baseUdFiles, $file))

            Write-Output "Current Input"
            Write-Output $input
            Write-Output "Creating file"
            Write-Output $output
            if ($pos -eq "with_possessive")
            {
                If ($nest -eq "flat")
                {
                    python chunker_runner.py $input $output "json" -l
                }
                else
                {
                    python chunker_runner.py $input $output "json" -l -n

                }
            }
            else
            {
                If ($nest -eq "flat")
                {
                    python chunker_runner.py $input $output "json" -l -np
                }
                else
                {
                    python chunker_runner.py $input $output "json" -l -n -np
                }
            }
        }

    }
}

foreach ($pos in $posOpt)
{
    foreach ($nest in $nestOpt)
    {
        $newDir = -join ($outBase, "\", $pos, "\", $nest)
        Write-Output "Creating a new folder in:"
        Write-Output $newDir
        New-Item -Path $newDir -ItemType Directory
        foreach ($file in $udFiles)
        {
            $out_file = $file.split('\.')[-2]
            $output = (-join ($newDir, "\", $out_file, ".txt"))
            $input = (-join ($baseUdFiles, $file))

            Write-Output "Current Input"
            Write-Output $input
            Write-Output "Creating file"
            Write-Output $output
            if ($pos -eq "with_possessive")
            {
                If ($nest -eq "flat")
                {
                    python chunker_runner.py $input $output "BIOSE" -l
                }
                else
                {
                    python chunker_runner.py $input $output "BIOSE" -l -n

                }
            }
            else
            {
                If ($nest -eq "flat")
                {
                    python chunker_runner.py $input $output "BIOSE" -l -np
                }
                else
                {
                    python chunker_runner.py $input $output "BIOSE" -l -n -np
                }
            }
        }

    }
}



