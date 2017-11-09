port module Main exposing (..)

import Html exposing (div, Html, text)
import Html.Attributes exposing (class, id)
import Html.Events exposing (onClick)
import WebSocket
import Json.Encode exposing (object, encode)
import Json.Decode exposing (int, field, list, Decoder, decodeString)
import Json.Decode.Pipeline exposing (decode, required, optional, hardcoded)


port beat : Int -> Cmd msg


type alias Flags =
    { websocketHost : String }


main : Program Flags Model Msg
main =
    Html.programWithFlags
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }



-- MODEL


type alias Model =
    { rhythm : List Rhythm
    , wsurl : String
    }


type Rhythm
    = Rest
    | Legato
    | Beat Int


intToRhythm : Int -> Rhythm
intToRhythm i =
    if i == -1 then
        Rest
    else if i == 0 then
        Legato
    else
        Beat (i - 1)


numPitches : Int
numPitches =
    4


init : Flags -> ( Model, Cmd Msg )
init fs =
    let
        url host =
            host ++ ":7700/colormonosequencer"

        getStateWSMsg =
            object [ ( "kind", Json.Encode.string "state" ) ]

        wsurl =
            Debug.log "url" (url fs.websocketHost)
    in
        ( Model [] wsurl, WebSocket.send wsurl <| encode 0 getStateWSMsg )



-- UPDATE


type Msg
    = RcvMsg String
    | SetRhythm Int Rhythm


type alias StateMsgPayload =
    { pitches : List Int
    , rhythm : List Int
    }


type alias StateMsg =
    { payload : StateMsgPayload
    }


type alias BeatMsg =
    { payload : BeatMsgPayload
    }


type alias BeatMsgPayload =
    { rhythmIndex : Int
    , noteIndex : Int
    }


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        RcvMsg wsmsg ->
            onReceiveWSMsg wsmsg model

        SetRhythm index newRhythm ->
            let
                setRhythm i currentRhythm =
                    if i == index then
                        newRhythm
                    else
                        currentRhythm

                newRhythms =
                    List.indexedMap setRhythm

                cmd =
                    WebSocket.send model.wsurl <| encode 0 <| changeRhythmWSMsg index newRhythm
            in
                ( { model | rhythm = newRhythms model.rhythm }, cmd )


onReceiveWSMsg : String -> Model -> ( Model, Cmd Msg )
onReceiveWSMsg wsmsg model =
    case decodeString (field "action" Json.Decode.string) wsmsg of
        Ok "state" ->
            ( updateState wsmsg model, Cmd.none )

        Ok "beat" ->
            let
                cmd =
                    case decodeString decodeBeatMsg wsmsg of
                        Ok b ->
                            beat b.payload.rhythmIndex

                        _ ->
                            Debug.crash "error decoding beat"
            in
                ( model, cmd )

        _ ->
            model ! []


decodeBeatMsg : Decoder BeatMsg
decodeBeatMsg =
    let
        payloadDecoder =
            decode BeatMsgPayload
                |> required "rhythm_index" int
                |> required "note_index" int
    in
        decode BeatMsg
            |> required "payload" payloadDecoder


updateState : String -> Model -> Model
updateState msg =
    let
        updater newState model =
            { model
                | rhythm = List.map intToRhythm newState.payload.rhythm
            }

        stateMsgDecoder =
            decode StateMsg
                |> required "payload" payloadDecoder

        payloadDecoder =
            decode StateMsgPayload
                |> required "pitches" (list int)
                |> required "rhythm" (list int)
    in
        case decodeString stateMsgDecoder msg of
            Ok newState ->
                updater newState

            _ ->
                Debug.crash ""



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    WebSocket.listen model.wsurl RcvMsg



-- VIEW


view : Model -> Html Msg
view model =
    div [ class "container" ] [ viewRhythms model.rhythm ]


viewRhythms : List Rhythm -> Html Msg
viewRhythms rhythms =
    div [ class "rhythm-container" ] <| List.indexedMap viewRhythmBox rhythms


viewRhythmBox : Int -> Rhythm -> Html Msg
viewRhythmBox i rhythm =
    let
        colorClass r =
            case r of
                Rest ->
                    "rest"

                Legato ->
                    "legato"

                Beat x ->
                    "color-" ++ (toString x)

        swatch j =
            div
                [ class <| "swatch " ++ (colorClass (intToRhythm j))
                , onClick <| SetRhythm i (Beat j)
                ]
                []

        palette =
            List.range -1 numPitches |> List.reverse |> List.map swatch
    in
        div [ class "rhythm-box-container", id <| "rhythm-" ++ (toString i) ]
            [ div [ class <| "rhythm-box " ++ (colorClass rhythm) ] []
            , div [ class "mini-palette" ] palette
            ]



-- COMMANDS


changeRhythmWSMsg : Int -> Rhythm -> Json.Encode.Value
changeRhythmWSMsg index rhythm =
    let
        value =
            case rhythm of
                Legato ->
                    0

                Rest ->
                    -1

                Beat x ->
                    x
    in
        object
            [ ( "kind", Json.Encode.string "rhythm" )
            , ( "payload"
              , object
                    [ ( "index", Json.Encode.int index )
                    , ( "value", Json.Encode.int value )
                    ]
              )
            ]
