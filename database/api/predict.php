<?php

header("Content-Type: application/json");

include "../config/database.php";

$sql = "SELECT * FROM predictions ORDER BY score DESC LIMIT 10";
$result = $conn->query($sql);

$data = [];

while($row = $result->fetch_assoc()){
    $data[] = $row;
}

echo json_encode($data);

?>