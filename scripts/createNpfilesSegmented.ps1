conda activate np
Write-Output "Python Running:"
which python
$baseUdFiles = "C:\Users\rafael\Desktop\studies\MSC\Theses\np_chunckers\heb_np_chuncker\corpus\model_seg\csv\seg_only_htb_"
$outBase = "C:\Users\rafael\Desktop\studies\MSC\Theses\np_chunckers\heb_np_chuncker\np_data\amit_seg\stanza_parse"

$segFiles = @("dev.csv", "test.csv")
$nestOpt = @("flat", "nested")
$posOpt = @("no_possessive", "with_possessive")

Set-Location "C:\Users\rafael\Desktop\studies\MSC\Theses\np_chunckers\heb_np_chuncker\"
foreach ($pos in $posOpt) {
    foreach ($nest in $nestOpt) {
            $newDir = -join($outBase, "\",$pos, "\",$nest)
            Write-Output "Creating a new folder in:"
            Write-Output $newDir
            New-Item -Path $newDir -ItemType Directory
        foreach ($file in $segFiles) {
            $out_file = $file.split('\.')[-2]
            $output = (-join($newDir,"\", $out_file, ".json"))
            $input = (-join($baseUdFiles, $file))

            Write-Output "Current Inpt"
            Write-Output $input
            Write-Output "Creating file"
            Write-Output $output
            if ($nest -eq "with_possessive") {

                If ($nest -eq "flat") {
                    python runner.py $input $output "BIOSE" "json" -ic -nn
                }
                else{
                   python runner.py $input $output "BIOSE" "json" -ic

                    }
            }
            else
            {
                If ($nest -eq "flat") {
                    python runner.py $input $output "BIOSE" "json" -ic -nn -np
                }
                else{
                    python runner.py $input $output "BIOSE" "json" -ic -np

                }

            }

        }
        }
    }






